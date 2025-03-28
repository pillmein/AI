# Python 3.9 기반 이미지 사용
FROM python:3.9

# 작업 디렉토리 설정
WORKDIR /app

# 필요한 파일 복사
COPY requirements.txt .
COPY api_analysis.py .
COPY api_sup_recommendation.py .
COPY api_time_recommendation.py .
COPY api_favorites.py .
COPY api_health_problem.py .
COPY api_ocr_analyze.py .
COPY config.py .

# 필수 패키지 설치
RUN pip install --no-cache-dir -r requirements.txt

# Supervisor 설치
RUN apt-get update && apt-get install -y supervisor

# Supervisor 설정 파일 복사
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# 컨테이너 실행 시 Supervisor 실행
CMD ["supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]