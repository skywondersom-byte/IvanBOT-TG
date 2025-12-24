# services/gemini_service.py

import google.generativeai as genai
import logging
import json
import asyncio
import random
from typing import Optional
from functools import wraps

from config import settings
from models import PropertyData
from .cache_service import cache
from utils.constants import RetryConfig

genai.configure(api_key=settings.GEMINI_API_KEY)

generation_config = genai.types.GenerationConfig(
    temperature=0.9,
)
model = genai.GenerativeModel(model_name="gemini-2.5-flash", generation_config=generation_config)

def retry_on_error(max_retries=RetryConfig.MAX_RETRIES, delay=RetryConfig.RETRY_DELAY):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        logging.error(f"All retries exhausted for {func.__name__}: {e}")
                        raise e
                    logging.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                    await asyncio.sleep(delay)
        return wrapper
    return decorator

@retry_on_error()
async def extract_base_data(text: str) -> Optional[PropertyData]:
    if not text:
        return None

    cached_data = cache.get(text, "base_data")
    if cached_data:
        logging.info("Using cached base data")
        return PropertyData(**cached_data)

    prompt = f"""
    Analyze this property rental listing text.
    Your task is to extract key information and return it in JSON format.

    Fields to extract:
    1. "type": Property type (e.g., "2-bedroom flat", "Studio", "Room"). Keep it concise, just the type.
    2. "price": Price (just the number and currency if available).
    3. "location": Area or address (e.g., "Stratford", "London, E15").

    Rules:
    - If any field cannot be found, set its value to "-".
    - Your response must be ONLY in JSON format.

    Text to analyze:
    ---
    {text}
    ---
    """
    try:
        json_gen_config = genai.types.GenerationConfig(response_mime_type="application/json", temperature=0.1)
        response = await model.generate_content_async(prompt, generation_config=json_gen_config)
        
        raw_data = json.loads(response.text)
        validated_data = PropertyData(**raw_data)
        
        cache.set(text, "base_data", validated_data.model_dump())
        return validated_data

    except Exception as e:
        logging.error(f"Error in extract_base_data: {e}")
        return None

async def generate_description(text: str, max_length: int, property_type: str, property_location: str, property_price: str) -> str | None:
    if not text or max_length <= 0:
        return ""

    random_seed = random.randint(1, 10000)

    styles = [
        "neutral_story",
        "location_focus",
        "comfort_focus"
    ]
    chosen_style = random.choice(styles)

    prompt = f"""
    Write a simple property rental listing for Telegram in English.

    INPUT DATA:
    - Property type: {property_type}
    - Location: {property_location}
    - Price: {property_price}
    - Details: {text}

    MAIN RULE - WRITE LIKE A REGULAR PERSON:
    - Imagine your friend is renting out their flat and asks you to write a listing
    - Write simply, without realtor clichés
    - No "perfect choice", "exquisite apartment", "offers amazing views"
    - No lists of additional services, social media, languages
    - Just describe the property, state the price, location, and contact

    STYLE (IMPERSONAL BUT SIMPLE):
    - Use: "Available", "For rent", "To let"
    - DON'T use first person ("I'm renting", "we offer")
    - Write briefly and to the point

    STRUCTURE (style for this post: {chosen_style}):

    1. "neutral_story" - just a story:
       "{property_type} available in {property_location}. [Brief amenities]. Rent is {property_price}. Phone: +447796029457 (Telegram)."

    2. "location_focus" - start with location:
       "In {property_location}, {property_type} available. [Description]. Rent {property_price}. Contact: +447796029457 (Telegram)."

    3. "comfort_focus" - focus on amenities:
       "{property_type} with [list of amenities]. Located in {property_location}, {property_price} per month. Contact: +447796029457 (Telegram)."

    IMPORTANT ABOUT DATES:
    - DO NOT mention availability dates (from/to dates)
    - Even if dates are in the input text, DO NOT include them in the listing
    - Write about the property as if it's simply available for rent

    FORBIDDEN PHRASES (realtor clichés):
    ❌ "exquisite apartment"
    ❌ "perfect choice"
    ❌ "ideal place for"
    ❌ "offers stunning views"
    ❌ "this is a great opportunity"
    ❌ "for comfortable stay"
    ❌ "happy to discuss"
    ❌ "other properties also available"
    ❌ "info on Facebook/Instagram"
    ❌ "communication possible"
    ❌ "for details and booking"

    ALLOWED PHRASES (simple, human):
    ✅ "cozy apartment"
    ✅ "spacious"
    ✅ "conveniently located"
    ✅ "has terrace/air conditioning"
    ✅ "nice views"
    ✅ "two bedrooms with bathrooms"

    LIMITATIONS:
    - Length up to {max_length} characters
    - No emojis
    - No icons 📍🏠💰
    - Only one contact: +447796029457 (Telegram)
    - DO NOT add information about other services, social media, or languages

    EXAMPLE OF CORRECT TEXT:
    "Cozy two-bedroom flat available on Earl's Court Road in Kensington. Has terrace, air conditioning, nice rooftop views. Each bedroom has its own bathroom. Rent is £4000 per month. Phone: +447796029457 (Telegram)."

    Write ONLY the listing text, no comments.
    """
    try:
        response = await model.generate_content_async(prompt)
        desc_text = response.text.strip()
        
        # Remove realtor phrases if AI added them anyway
        spam_phrases = [
            "Other properties also available",
            "Info on Facebook",
            "Communication possible",
            "including entire accommodations",
            "which can be selected",
            "Tik-Tok",
            "Instagram",
            "in English, Ukrainian, Russian, Polish",
            "for details and booking",
            "happy to discuss details",
            "Available from",
            "To let from",
            "until",
            "to",
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December",
            "2024",
            "2025",
            "2026"
        ]
        
        for phrase in spam_phrases:
            if phrase in desc_text:
                sentences = desc_text.split('.')
                filtered = [s for s in sentences if phrase not in s]
                desc_text = '.'.join(filtered)
        
        # Safety: if AI forgot to add phone, add it
        target_phone = "+447796029457 (Telegram)"
        if "447796029457" not in desc_text:
            connectors = ["Phone:", "Contact:", "Tel:"]
            connector = random.choice(connectors)
            desc_text = desc_text.rstrip('.') + f". {connector} {target_phone}"
        
        # Remove greetings
        forbidden_starts = ["Hello everyone", "Hello", "Hi", "Good day"]
        for start in forbidden_starts:
            if desc_text.lower().startswith(start.lower()):
                parts = desc_text.split('.', 1)
                if len(parts) > 1:
                    desc_text = parts[1].strip()

        logging.info(f"GEMINI (description): Style {chosen_style}, Length {len(desc_text)}")
        return desc_text
    except Exception as e:
        logging.error(f"Error generating description: {e}", exc_info=True)
        return None