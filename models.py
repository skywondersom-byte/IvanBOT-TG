from pydantic import BaseModel, Field, field_validator
from typing import Optional

class PropertyData(BaseModel):
    type: str = Field(default="-")
    price: str = Field(default="-")
    location: str = Field(default="-")
    phone: str = Field(default="-")  # Додано поле для телефону
    
    @field_validator('type', 'price', 'location', 'phone', mode='before')
    @classmethod
    def empty_str_to_dash(cls, v):
        if isinstance(v, str) and not v.strip():
            return "-"
        return v if v else "-"

class PostData(BaseModel):
    base_data: PropertyData
    description: str
    caption: str
    
    @field_validator('caption')
    @classmethod
    def validate_caption_length(cls, v):
        if len(v) > 4096:
            raise ValueError("Caption занадто довгий")
        return v