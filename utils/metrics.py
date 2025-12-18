from dataclasses import dataclass
from datetime import datetime
import logging

@dataclass
class BotMetrics:
    processed_posts: int = 0
    failed_posts: int = 0
    gemini_calls: int = 0
    start_time: datetime = datetime.now()
    
    def log_stats(self):
        uptime = datetime.now() - self.start_time
        logging.info(
            f" Статистика бота: Оброблено: {self.processed_posts}, "
            f"Помилок: {self.failed_posts}, Gemini викликів: {self.gemini_calls}, "
            f"Час роботи: {uptime}"
        )

metrics = BotMetrics()
