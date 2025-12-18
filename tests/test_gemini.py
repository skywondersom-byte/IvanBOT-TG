import sys
import os

# --- ВИПРАВЛЕННЯ ШЛЯХІВ ---
# Додаємо кореневу папку проекту до системних шляхів, 
# щоб Python міг побачити папки 'services', 'models' та 'utils'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# ---------------------------

import pytest
from services.gemini_service import extract_base_data
from models import PropertyData

# Маркуємо тест як асинхронний
@pytest.mark.asyncio
async def test_extract_base_data_valid():
    text = "2 Bedroom flat in Stratford for £1500 pcm + bills"
    result = await extract_base_data(text)
    
    assert result is not None
    assert isinstance(result, PropertyData)
    assert result.type != "-"
    # Перевіряємо, що ціна знайдена (хоча б частково)
    assert result.price != "-"
    assert "Stratford" in result.location or result.location != "-"

@pytest.mark.asyncio
async def test_extract_base_data_empty():
    result = await extract_base_data("")
    assert result is None

@pytest.mark.asyncio
async def test_extract_base_data_nonsense():
    # Тест на текст, який не є оголошенням
    text = "Просто випадковий набір слів без сенсу"
    # Очікуємо або None, або об'єкт з дефісами
    result = await extract_base_data(text)
    if result:
        assert result.type == "-" or result.price == "-"