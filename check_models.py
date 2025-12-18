# check_models.py
import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get your API key
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("Error: GEMINI_API_KEY not found in .env file.")
else:
    try:
        genai.configure(api_key=api_key)

        print("Fetching available models...\n")
        for model in genai.list_models():
            # We are looking for models that support 'generateContent'
            if 'generateContent' in model.supported_generation_methods:
                print(f"Model Name: {model.name}")
                print("-" * 20)

    except Exception as e:
        print(f"An error occurred: {e}")