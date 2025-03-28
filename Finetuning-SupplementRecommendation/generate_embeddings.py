import numpy as np
import pickle
from sentence_transformers import SentenceTransformer
from gpt_sup_recommendation import fetch_data_from_db

# DB에서 데이터 로드
df_items = fetch_data_from_db()

# 텍스트 데이터 구성
text_data = df_items.apply(
    lambda row: f"제품명: {row['name']}, 효과: {row['effects']}, 원재료: {row['ingredients']}, 경고사항: {row['warnings']}",
    axis=1
).tolist()

# SentenceTransformer 모델
model_name = 'sentence-transformers/all-MiniLM-L6-v2'
embedder = SentenceTransformer(model_name)

# 테이블 컬럼에 맞춰 텍스트 데이터 구성
text_data = df_items.apply(
    lambda row: f"제품명: {row['name']}, 효과: {row['effects']}, 원재료: {row['ingredients']}, 경고사항: {row['warnings']}",
    axis=1
).tolist()

# 임베딩 생성
embeddings = embedder.encode(text_data)

# 파일로 저장
np.save("../embeddings.npy", embeddings)  # NumPy 배열 저장
with open("../index.pkl", "wb") as f:
    pickle.dump(df_items, f)  # 데이터프레임 저장

print("✅ 임베딩 및 데이터 저장 완료!")