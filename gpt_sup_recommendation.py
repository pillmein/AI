import pandas as pd
import psycopg2
import faiss
import openai
import numpy as np
import pickle
from config import OPENAI_API_KEY, FINE_TUNED_MODEL_ID
from sentence_transformers import SentenceTransformer

# OpenAI API 키 설정
openai.api_key = OPENAI_API_KEY
model_name = 'sentence-transformers/all-MiniLM-L6-v2'
embedder = SentenceTransformer(model_name)


# PostgreSQL에서 데이터 가져오기
def fetch_data_from_db():
    try:
        # PostgreSQL 연결
        conn = psycopg2.connect(
            host="127.0.0.1",  # 또는 클라우드 DB 주소
            port="5432",  # PostgreSQL 포트
            database="test",  # 데이터베이스 이름
            user="postgres",  # 사용자 이름
            password="ummong1330"  # 비밀번호
        )
        query = "SELECT id, effects, ingredients, name, warnings FROM api_supplements"
        df = pd.read_sql(query, conn)
        conn.close()
        print("✅ 데이터 로드 성공!")
        return df
    except Exception as e:
        print(f"❌ 데이터 로드 실패: {e}")
        return None


def fetch_user_supplements(user_id):
    """사용자가 복용 중인 영양제 정보를 데이터베이스에서 가져오는 함수"""
    try:
        conn = psycopg2.connect(
            host="127.0.0.1",
            port="5432",
            database="test",
            user="postgres",
            password="ummong1330"
        )
        query = f"""
        SELECT supplement_name, ingredients
        FROM user_supplements
        WHERE user_id = {user_id}
        """
        df_user_supplements = pd.read_sql(query, conn)
        conn.close()

        if df_user_supplements.empty:
            print("⚠️ 사용자가 현재 복용 중인 영양제가 없습니다.")
            return None

        return df_user_supplements

    except Exception as e:
        print(f"❌ 사용자 복용 영양제 데이터 로드 실패: {e}")
        return None


def load_data():
    """데이터를 로드하고 임베딩을 생성하는 함수"""
    print("✅ 데이터 로드 중...")
    df_items = fetch_data_from_db()

    if df_items is not None:
        """
        # 1. SentenceTransformer로 텍스트 임베딩 생성
        model_name = 'sentence-transformers/all-MiniLM-L6-v2'
        embedder = SentenceTransformer(model_name)

        # 테이블 컬럼에 맞춰 텍스트 데이터 구성
        text_data = df_items.apply(
            lambda row: f"제품명: {row['name']}, 효과: {row['effects']}, 원재료: {row['ingredients']}, 경고사항: {row['warnings']}",
            axis=1
        ).tolist()

        embeddings = embedder.encode(text_data)
        """

        # 저장된 임베딩 로드
        embeddings = np.load("embeddings.npy")
        # 데이터프레임 로드
        with open("index.pkl", "rb") as f:
            df_items = pickle.load(f)

        # 2. FAISS 인덱스에 임베딩 추가
        dimension = embeddings.shape[1]  # 임베딩 벡터 차원
        index = faiss.IndexFlatL2(dimension)
        index.add(embeddings)

        print("✅ 데이터 로드 및 임베딩 생성 완료!")

        return df_items, index  # 데이터를 반환

    else:
        print("❌ 데이터프레임이 None이므로 실행을 중단합니다.")
        return None, None, None


def search(query, df_items, embedder, index, k=3):
    """유사한 제품을 검색하는 함수"""
    query_embedding = embedder.encode([query])
    distances, indices = index.search(query_embedding, k)
    results = df_items.iloc[indices[0]]
    return results


def generate_health_summary(survey_data):
    """사용자의 건강 설문 데이터를 기반으로 건강 상태 요약을 생성하는 함수"""
    # 1) LLM이 이해할 수 있는 Context 생성
    context = "\n".join([
        f"- 질문: {item['question']}\n  응답: {item['answer']}\n  우려사항: {item['concern']}\n  필요한 영양소: {', '.join(item['required_nutrients']) if isinstance(item['required_nutrients'], list) else item['required_nutrients']}"
        for item in survey_data
    ])

    # 2) GPT에 전달할 프롬프트 작성
    prompt = f"""
    당신은 전문 건강 분석 AI입니다. 아래 건강 설문 데이터를 기반으로 각 항목에 대해 답변을 해석하고, 우선순위를 매기세요. 반드시 한국어로 답하세요.

    건강 설문 데이터:
    {context}

    답변 형식:
    1순위: "사용자는 [응답]하므로, [우려사항]이 가장 우려됩니다. 이에 따라 [필요한 영양소] 보충이 필요할 수 있습니다."
    2순위: "사용자는 [응답]하므로, [우려사항]이 두 번째로 우려됩니다. 이에 따라 [필요한 영양소] 보충이 필요할 수 있습니다."
    3순위: "사용자는 [응답]하므로, [우려사항]이 세 번째로 우려됩니다. 이에 따라 [필요한 영양소] 보충이 필요할 수 있습니다."

    답변 예시:
    1순위: 사용자는 매우 자주 시력이 저하되거나 눈이 피로해지므로, 시력 저하와 안구 건조증이 우려됩니다. 이에 따라 비타민 A, 오메가-3 지방산 보충이 필요할 수 있습니다.

    심각도 기준:
    - 만성 질환 관련 문제는 높은 우선순위
    - 식습관이 매우 불균형할 경우 높은 우선순위
    - 특정 영양소 결핍 위험이 클 경우 높은 우선순위

    사용자가 '매우 자주 있음'이라고 응답한 문제가 가장 심각한 문제인 것으로 판단하고, 건강 데이터를 기반으로 우선순위를 결정하세요.

    이제 사용자의 건강 상태를 답변 형식에 맞게 1~3순위로 정리하고, 그 근거를 함께 제시하세요.
    """

    # 3) GPT API 호출
    response = openai.chat.completions.create(
        model=FINE_TUNED_MODEL_ID,  # 파인튜닝된 모델 사용
        messages=[
            {"role": "system", "content": "You are an AI health expert providing concise health summaries."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=500
    )

    return response.choices[0].message.content


def rag_qa_system(question, df_items, index, user_id):
    """GPT-3.5 Turbo를 이용한 RAG 시스템"""
    if df_items is None or index is None:
        print("❌ 데이터가 로드되지 않았습니다. 먼저 load_data()를 실행하세요.")
        return None

    # 사용자가 복용 중인 영양제 가져오기
    df_user_supplements = fetch_user_supplements(user_id)

    # 1) Retrieve: 유사한 데이터 검색
    search_results = search(question, df_items, embedder, index)

    # 2) Context 생성
    context = "\n".join(
        f"제품명: {row['name']}, 효과: {row['effects']}, 원재료: {row['ingredients']}, 경고사항: {row['warnings']}"
        for _, row in search_results.iterrows()
    )

    # 3) 사용자 복용 영양제 정보 생성
    if df_user_supplements is not None:
        user_supplements_context = "\n".join(
            f"- {row['supplement_name']} (주요 성분: {row['ingredients']})"
            for _, row in df_user_supplements.iterrows()
        )
    else:
        user_supplements_context = "사용자는 현재 복용 중인 영양제가 없습니다."

    # 4) LLM에 질의와 컨텍스트 전달하여 답변 생성
    prompt = f"""
    당신은 건강 보조제 추천 전문가입니다. 사용자의 질문에 대해 아래 제공된 참고 정보에서 가장 관련이 있는 제품명을 찾아 추천해주세요.

    참고 정보:
    {context}

    사용자가 복용 중인 영양제 정보:
    {user_supplements_context}

    질문: {question}

    반드시 다음과 같은 형식으로 3가지 건강 문제와 각각의 추천 영양제를 제시하세요:

    1. 건강 문제: (건강 문제 1)
       추천 영양제: (제품명 1)
       주요 원재료: (영양제 1의 주요 원재료)
       효과: (영양제 1의 효과)

    2. 건강 문제: (건강 문제 2)
       추천 영양제: (제품명 2)
       주요 원재료: (영양제 2의 주요 원재료)
       효과: (영양제 2의 효과)

    3. 건강 문제: (건강 문제 3)
       추천 영양제: (제품명 3)
       주요 원재료: (영양제 3의 주요 원재료) 
       효과: (영양제 3의 효과)

    위의 형식을 유지하고, 제공된 참고 정보에서 적절한 제품을 선택하여 추천하세요.
    참고 정보에서 사용자의 영양제 섭취 목적(건강 목표)을 고려하여 추천하세요.
    사용자에게 필요한 영양성분 여러 가지가 동시에 포함되어 있는 영양제를 우선적으로 추천하세요.
    영양제의 부원료와 주요성분의 시너지 효과를 고려하여 추천하세요. 같은 주요 성분이라도 부원료(보조 성분)에 따라 흡수율 & 효과 차이 발생
    예를 들어:
        칼슘 보충 → "비타민 D & K2 포함된 제품"이 흡수율 증가
        철분 보충 → "비타민 C 포함된 제품"이 흡수율 증가
        관절 건강 → "콜라겐 + 히알루론산 + MSM" 포함된 제품 추천
    ⚠️ 현재 복용 중인 영양제의 성분과 중복되는 경우 추천하지 마세요.
    """

    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system",
             "content": "You are an assistant that provides specific supplement recommendations based on nutrients."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=800
    )
    return response.choices[0].message.content


# 직접 실행할 경우만 load_data() 실행
if __name__ == "__main__":
    df_items, index = load_data()