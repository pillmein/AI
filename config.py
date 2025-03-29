import os

OPENAI_API_KEY = "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"  # 🔹 OpenAI API 키 입력 필요
FINE_TUNED_MODEL_ID = "ft:gpt-3.5-turbo-0125:personal::B0LjeTdb"
SECRET_KEY = "EvmYUavrGG7FBnjXFrAVyv2pSpkwPE/jO2j/ecC4vz4="
GOOGLE_APPLICATION_CREDENTIALS = "helical-history-450910-v7-9d92c447277a.json"
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "port": os.getenv("DB_PORT", "5432"),
    "database": os.getenv("DB_NAME", "test"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "ummong1330")
}