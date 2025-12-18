from aiogram import Router
from aiogram.types import ErrorEvent
import logging
from utils.metrics import metrics

error_router = Router()

@error_router.error()
async def error_handler(event: ErrorEvent):
    logging.error(f"🚨 Критична помилка обробника: {event.exception}", exc_info=True)
    metrics.failed_posts += 1
    
    # Спроба повідомити користувача (якщо це можливо)
    if hasattr(event, 'update') and event.update.message:
        try:
            # Не завжди доречно відповідати юзеру в каналі, але для тестів корисно
            # await event.update.message.answer("⚠️ Сталася технічна помилка.")
            pass 
        except:
            pass