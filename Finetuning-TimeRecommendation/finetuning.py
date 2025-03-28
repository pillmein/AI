import openai
from config import OPENAI_API_KEY

# OpenAI API 키 설정
openai.api_key = OPENAI_API_KEY

# 새로운 데이터셋 업로드
response = openai.files.create(
    file=open("dataset.jsonl", "rb"),
    purpose="fine-tune"
)
file_id = response.id
print(f"✅ 데이터 업로드 완료! 파일 ID: {file_id}")

# Fine-tuning 실행
fine_tune_response = openai.fine_tuning.jobs.create(
    training_file=file_id,
    model="gpt-3.5-turbo"
)
fine_tune_id = fine_tune_response.id
print(f"🚀 Fine-tuning 시작! Fine-tune ID: {fine_tune_id}")

# 학습 진행 상태 확인
status = openai.fine_tuning.jobs.retrieve(fine_tune_id)
print(f"✅ 현재 상태: {status.status}")

# Fine-tuned 모델 ID 가져오기
fine_tune_info = openai.fine_tuning.jobs.retrieve(fine_tune_id)
fine_tuned_model = fine_tune_info.fine_tuned_model

if fine_tuned_model:
    print(f"✅ Fine-tuned 모델 ID: {fine_tuned_model}")
else:
    print("❌ Fine-tuning이 완료되었지만 모델 ID를 찾을 수 없습니다.")