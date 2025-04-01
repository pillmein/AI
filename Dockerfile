# Base image
FROM python:3.9.6-buster

# 작업 디렉토리 설정
WORKDIR /app

# 필요한 파일 복사
COPY . /app

# 패키지 설치
RUN pip install -r requirements.txt

# Flask 실행 (main.py 사용)
CMD ["python", "main.py"]