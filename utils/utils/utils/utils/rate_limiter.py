import asyncio
from collections import deque
from datetime import datetime, timedelta
import logging

class RateLimiter:
    def __init__(self, max_calls: int, time_window: int):
        self.max_calls = max_calls
        self.time_window = timedelta(seconds=time_window)
        self.calls = deque()
    
    async def acquire(self):
        now = datetime.now()
        
        # Видалити старі виклики, які вийшли за межі вікна
        while self.calls and self.calls[0] < now - self.time_window:
            self.calls.popleft()
        
        # Якщо ліміт досягнуто, чекаємо
        if len(self.calls) >= self.max_calls:
            sleep_time = (self.calls[0] + self.time_window - now).total_seconds()
            if sleep_time > 0:
                logging.warning(f"⏳ Rate limit досягнуто. Очікування {sleep_time:.2f}с")
                await asyncio.sleep(sleep_time)
        
        self.calls.append(now)