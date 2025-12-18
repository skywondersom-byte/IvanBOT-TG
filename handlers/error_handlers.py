from aiogram import Router
from aiogram.types import ErrorEvent
import logging
from utils.metrics import metrics

error_router = Router()

@error_router.error()
async def error_handler(event: ErrorEvent):
    logging.error(f"🚨 Критична помилка обробника: {event.exception}", exc_info=True)
    metrics.failed_posts += 1
