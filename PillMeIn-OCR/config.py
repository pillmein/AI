"""
This module contains the configuration settings for the application.

import json

class Config:
    #Configuration class for the application.
    # config.json 파일을 읽어서 경로를 저장
    with open('config.json') as config_file:
        config = json.load(config_file)

    SQLALCHEMY_DATABASE_URI = config.get('DATABASE_URL')
    PRESTO_URI = config.get('ENGINE_URI')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = config.get('DEBUG', False)
"""

GOOGLE_APPLICATION_CREDENTIALS = "helical-history-450910-v7-9d92c447277a.json"
OPENAI_API_KEY = "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"  # 🔹 OpenAI API 키 입력 필요