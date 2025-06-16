import openai
from config import OPENAI_API_KEY

openai.api_key = OPENAI_API_KEY

# 확인할 Fine-tune ID 입력
fine_tune_id = "ftjob-g9Tggwn1cZu5DeNS4jfJWIOk"

# 상태 확인
status = openai.fine_tuning.jobs.retrieve(fine_tune_id)

# 상태 출력
print(f"📊 현재 상태: {status.status}")
print(f"📅 생성 시각: {status.created_at}")
print(f"📦 사용 모델: {status.model}")
print(f"📁 학습 파일 ID: {status.training_file}")
print(f"📦 결과 모델: {status.fine_tuned_model}")
