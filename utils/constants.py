class MessageLimits:
    MAX_CAPTION_WITH_MEDIA = 1024
    MAX_TEXT_MESSAGE = 4096

class RetryConfig:
    MAX_RETRIES = 3
    RETRY_DELAY = 2

class AlbumConfig:
    COLLECTION_TIMEOUT = 1.5

# Футер тепер порожній, бо контактні дані інтегруються всередину тексту AI
FOOTER_TEMPLATE = ""