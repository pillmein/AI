import pandas as pd
import psycopg2
from sentence_transformers import SentenceTransformer
import faiss
import openai
from config import OPENAI_API_KEY

# OpenAI API 키 설정
openai.api_key = OPENAI_API_KEY

# PostgreSQL에서 데이터 가져오기
def fetch_data_from_db():
    try:
        # PostgreSQL 연결
        conn = psycopg2.connect(
            host="127.0.0.1",  # 또는 클라우드 DB 주소
            port="5432",        # PostgreSQL 포트
            database="test",    # 데이터베이스 이름
            user="postgres",    # 사용자 이름
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

def load_data():
    """데이터를 로드하고 임베딩을 생성하는 함수"""
    print("✅ 데이터 로드 중...")
    df_items = fetch_data_from_db()

    if df_items is not None:
        # 1. SentenceTransformer로 텍스트 임베딩 생성
        model_name = 'sentence-transformers/all-MiniLM-L6-v2'
        embedder = SentenceTransformer(model_name)

        # 테이블 컬럼에 맞춰 텍스트 데이터 구성
        text_data = df_items.apply(
            lambda row: f"제품명: {row['name']}, 효과: {row['effects']}, 원재료: {row['ingredients']}, 경고사항: {row['warnings']}",
            axis=1
        ).tolist()

        embeddings = embedder.encode(text_data)

        # 2. FAISS 인덱스에 임베딩 추가
        dimension = embeddings.shape[1]  # 임베딩 벡터 차원
        index = faiss.IndexFlatL2(dimension)
        index.add(embeddings)

        print("✅ 데이터 로드 및 임베딩 생성 완료!")

        return df_items, embedder, index  # 데이터를 반환

    else:
        print("❌ 데이터프레임이 None이므로 실행을 중단합니다.")
        return None, None, None

def search(query, df_items, embedder, index, k=3):
    """유사한 제품을 검색하는 함수"""
    query_embedding = embedder.encode([query])
    distances, indices = index.search(query_embedding, k)
    results = df_items.iloc[indices[0]]
    return results

def rag_qa_system(question, df_items, embedder, index):
    """GPT-3.5 Turbo를 이용한 RAG 시스템"""
    if df_items is None or embedder is None or index is None:
        print("❌ 데이터가 로드되지 않았습니다. 먼저 load_data()를 실행하세요.")
        return None

    # 1) Retrieve: 유사한 데이터 검색
    search_results = search(question, df_items, embedder, index)

    # 2) Context 생성
    context = "\n".join(
        f"제품명: {row['name']}, 효과: {row['effects']}, 원재료: {row['ingredients']}, 경고사항: {row['warnings']}"
        for _, row in search_results.iterrows()
    )

    # 3) LLM에 질의와 컨텍스트 전달하여 답변 생성
    prompt = f"""
    당신은 건강 보조제 추천 전문가입니다. 사용자의 질문에 대해 아래 제공된 참고 정보에서 가장 관련이 있는 제품명을 찾아 추천해주세요.

    참고 정보:
    {context}

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
    """

    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an assistant that provides specific supplement recommendations based on nutrients."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=800
    )
    return response.choices[0].message.content

# 직접 실행할 경우만 load_data() 실행
if __name__ == "__main__":
    df_items, embedder, index = load_data()
