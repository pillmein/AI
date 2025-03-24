import openai
from config import OPENAI_API_KEY

# OpenAI API 키 설정
openai.api_key = OPENAI_API_KEY

fine_tune_info = openai.fine_tuning.jobs.retrieve("ftjob-4H8guCm279bvZuMP1jg2lLSY")
fine_tuned_model = fine_tune_info.fine_tuned_model

if fine_tuned_model:
    print(f"✅ Fine-tuned 모델 ID: {fine_tuned_model}")
else:
    print("❌ 아직 모델 ID가 생성되지 않았습니다.")
