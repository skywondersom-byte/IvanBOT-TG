from typing import Optional, Dict, Any
import hashlib
import logging

class SimpleCache:
    def __init__(self):
        self._cache: Dict[str, Any] = {}
    
    def _make_key(self, text: str, operation: str) -> str:
        # Створюємо унікальний хеш ключа з тексту та назви операції
        return hashlib.md5(f"{operation}:{text}".encode()).hexdigest()
    
    def get(self, text: str, operation: str) -> Optional[Dict[str, Any]]:
        key = self._make_key(text, operation)
        data = self._cache.get(key)
        if data:
            logging.debug(f"CACHE HIT: {operation}")
        return data
    
    def set(self, text: str, operation: str, data: Dict[str, Any], ttl: int = 3600):
        key = self._make_key(text, operation)
        self._cache[key] = data
        logging.debug(f"CACHE SET: {operation}")
        # Примітка: Для production краще використовувати Redis з автоматичним TTL

cache = SimpleCache()