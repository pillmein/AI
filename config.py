import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
FINE_TUNED_MODEL_ID = os.getenv("FINE_TUNED_MODEL_ID")
SECRET_KEY = os.getenv("SECRET_KEY")
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")


DB_CONFIG = {
    "host": "127.0.0.1",
    "port": "5432",
    "database": "test",
    "user": "postgres",
    "password": "ummong1330"
}