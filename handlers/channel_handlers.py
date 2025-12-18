# handlers/channel_handlers.py

import asyncio
import logging
import random
from typing import Dict, List, Union

from aiogram import Bot, F, Router
from aiogram.types import InputMediaPhoto, InputMediaVideo, Message

from config import settings
from services.gemini_service import extract_base_data, generate_description
from utils.constants import MessageLimits, AlbumConfig, FOOTER_TEMPLATE

channel_router = Router()
channel_router.channel_post.filter(F.chat.id == settings.SOURCE_CHANNEL_ID)

album_cache: Dict[str, List[Message]] = {}

async def process_post(messages: List[Message], bot: Bot, is_album: bool):
    if is_album:
        messages.sort(key=lambda x: x.message_id)
        message = messages[0]
        post_text = ""
        for m in messages:
            if m.caption:
                post_text = m.caption
                break
        logging.info(f"Обробляю альбом {message.media_group_id} ({len(messages)} медіа).")
    else:
        message = messages[0]
        post_text = message.text or message.caption
        logging.info(f"Обробляю пост {message.message_id}.")

    async def copy_original():
        if is_album:
            logging.warning(f"Пропускаю альбом {message.media_group_id} (помилка обробки).")
        else:
            await bot.copy_message(
                chat_id=settings.TARGET_CHANNEL_ID, 
                from_chat_id=message.chat.id, 
                message_id=message.message_id
            )
            await asyncio.sleep(1)

    if not post_text:
        await copy_original()
        return

    # Крок 1: Базові дані
    base_data = await extract_base_data(post_text)
    if not base_data:
        logging.error(f"Не вдалося витягнути дані для {message.message_id}.")
        await copy_original()
        return

    # Крок 2: Розрахунок довжини
    MAX_CAPTION = MessageLimits.MAX_CAPTION_WITH_MEDIA if (message.photo or message.video) else MessageLimits.MAX_TEXT_MESSAGE

    # Тепер вся інформація буде вплетена в текст, тому резервуємо мінімальний запас
    # лише на випадок, якщо AI не включить щось в текст
    SAFETY_MARGIN = 50  # Невеликий запас на випадок додавання телефону
    available_length = MAX_CAPTION - SAFETY_MARGIN
    
    # Крок 3: Генеруємо опис, передаючи всі дані
    # Тепер generate_description отримає ціну і сам вплете все в текст
    description = await generate_description(
        post_text, 
        available_length, 
        base_data.type, 
        base_data.location,
        base_data.price  # Додали ціну
    )
    
    if not description:
        logging.error(f"Не вдалося згенерувати опис для {message.message_id}.")
        await copy_original()
        return

    # Крок 4: Фінальний текст - це просто згенерований опис
    # Більше НІЯКИХ додавань підвалу, іконок чи списків!
    new_caption = description.strip()

    # Надсилання
    try:
        if is_album:
            media_group = []
            for i, msg in enumerate(messages):
                cap = new_caption if i == 0 else None
                if msg.photo:
                    media_group.append(InputMediaPhoto(media=msg.photo[-1].file_id, caption=cap, parse_mode="HTML"))
                elif msg.video:
                    media_group.append(InputMediaVideo(media=msg.video.file_id, caption=cap, parse_mode="HTML"))
            await bot.send_media_group(chat_id=settings.TARGET_CHANNEL_ID, media=media_group)
            logging.info(f"✅ Альбом {message.media_group_id} успішно надіслано.")
        else:
            await bot.copy_message(
                chat_id=settings.TARGET_CHANNEL_ID,
                from_chat_id=message.chat.id,
                message_id=message.message_id,
                caption=new_caption,
                parse_mode="HTML",
                reply_markup=message.reply_markup
            )
            logging.info(f"✅ Пост {message.message_id} успішно надіслано.")
        await asyncio.sleep(1)
    except Exception as e:
        logging.error(f"Помилка надсилання {message.message_id}: {e}")
        # За бажанням можна розкоментувати для фоллбеку
        # await copy_original() 

@channel_router.channel_post()
async def universal_post_handler(message: Message, bot: Bot):
    if message.media_group_id:
        group_id = str(message.media_group_id)
        if group_id not in album_cache:
            album_cache[group_id] = []
        album_cache[group_id].append(message)
        await asyncio.sleep(AlbumConfig.COLLECTION_TIMEOUT)

        if group_id in album_cache and message.message_id == album_cache[group_id][-1].message_id:
            msgs = album_cache.pop(group_id)
            await process_post(msgs, bot, is_album=True)
        return
        
    await process_post([message], bot, is_album=False)