from flask import Flask, request, jsonify, Blueprint
from flasgger import Swagger
import openai
import psycopg2
import re
from datetime import datetime
from flasgger import swag_from
from sentence_transformers import SentenceTransformer
from config import OPENAI_API_KEY, SECRET_KEY, FINE_TUNED_MODEL_ID, DB_CONFIG
from flask_jwt_extended import JWTManager, get_jwt_identity, jwt_required

# OpenAI API 키 설정
openai.api_key = OPENAI_API_KEY
# SentenceTransformer 전역변수 선언
model_name = 'sentence-transformers/all-MiniLM-L6-v2'
embedder = SentenceTransformer(model_name)

# Flask 인스턴스 생성
blueprint = Blueprint('time_recommendation_api', __name__)

# ✅ Swagger에서 Access Token 입력 필드 추가
swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "Time Recommendation API",
        "description": "영양제 복용 시간 추천 API",
        "version": "1.0.0"
    },
    "securityDefinitions": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "액세스 토큰을 입력하세요. (예: Bearer your_access_token)"
        }
    },
    "security": [{"Bearer": []}]
}


def normalize_ingredient(ingredient):
    """LLM을 사용하여 성분명을 일반적인 영양소명으로 변환"""
    prompt = f"""
    아래 성분명을 보다 일반적인 영양소 이름으로 변환해 주세요.

    예시:
    - 분리대두단백 → 단백질
    - 아세로라 추출물 → 비타민 C
    - 비타민B1 → 비타민 B
    - 히알루론산 → 히알루론산 (그대로 유지)

    성분명: {ingredient}
    변환된 영양소명:
    """

    response = openai.chat.completions.create(
        model=FINE_TUNED_MODEL_ID,
        messages=[
            {"role": "system", "content": "당신은 영양 성분을 일반 영양소명으로 변환하는 AI입니다."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=20
    )

    return response.choices[0].message.content.strip()


def extract_time(text):
    """응답에서 구체적인 시간을 추출하여 HH:MM:SS 형식으로 변환"""
    time_mapping = {
        "새벽": "06:00",
        "아침 공복": "08:00",
        "아침 식후": "09:00",
        "점심 공복": "12:00",
        "점심 식후": "13:30",
        "저녁 공복": "18:00",
        "저녁 식후": "19:30",
        "자기 전": "22:30"
    }

    for key, value in time_mapping.items():
        if key in text:
            return value

    # 정규식으로 숫자가 포함된 시간 패턴 추출 (예: "오전 8시", "오후 7시")
    match = re.search(r'(오전|오후)?\s*(\d{1,2})시', text)
    if match:
        period, hour = match.groups()
        hour = int(hour)
        if period == "오후" and hour < 12:
            hour += 12
        return f"{hour:02}:00:00"

    return "00:00"  # 기본값 (추출 실패 시)


@blueprint.route("/supplement-timing", methods=["POST"])
@jwt_required()
@swag_from({
    'tags': ['Supplement Timing'],
    'summary': '영양제의 주성분을 기반으로 최적 섭취 시간을 추천합니다.',
    'parameters': [
        {
            'name': 'user_supplement_id',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'supplementId': {'type': 'integer', 'example': 5}
                }
            }
        }
    ],
    "security": [{"Bearer": []}],
    'responses': {
        200: {
            'description': '최적 섭취 시간 반환',
            'schema': {
                'type': 'object',
                'properties': {
                    'advice': {'type': 'string'},
                    'optimalTimeFormatted': {'type': 'string'}
                }
            }
        },
        400: {'description': '잘못된 요청 (ID 없음)'},
        404: {'description': '해당 영양제를 찾을 수 없음'},
        500: {'description': '서버 오류'}
    }
})
def supplement_timing():
    """영양제의 주성분을 기반으로 최적 섭취 시간을 추천하는 API"""
    data = request.json
    supplement_id = data.get("supplementId")

    if not supplement_id:
        return jsonify({"error": "supplementId 값이 필요합니다."}), 400
    user_id = get_jwt_identity()

    try:
        # 1. DB에서 supplementId와 user_id가 일치하는 데이터의 성분 정보 조회
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        query = """
                SELECT ingredients FROM user_supplements 
                WHERE id = %s AND user_id = %s
                """
        cur.execute(query, (supplement_id, user_id))
        result = cur.fetchone()

        if not result:
            return jsonify({"error": "해당 영양제를 찾을 수 없습니다."}), 404

        ingredients = result[0]  # DB에서 가져온 성분 문자열

        # 2. 주성분(ingredients에서 첫 번째 성분) 추출 후 일반화
        ingredient_list = ingredients.split(",")
        main_ingredient = ingredient_list[0].strip() if ingredient_list else "알 수 없음"
        #generalized_ingredient = normalize_ingredient(main_ingredient)

        # 3. LLM에게 최적의 섭취 시간 질문
        prompt = f"""
        {main_ingredient}을 언제 복용하는 것이 가장 좋은가요? 
        연구 결과에 따르면 최적의 섭취 시간대가 언제인지 구체적인 시간과 함께 설명해주세요.
        아래 8가지 시간대 중 하나를 선택하여 답변하세요: 
        "새벽, 아침 공복, 아침 식후, 점심 공복, 점심 식후, 저녁 공복, 저녁 식후, 자기 전"

        연구 결과가 부족한 경우, 아래 영양성분 별 최적의 복용 시간을 참고하세요:
        - 비타민 B: 아침 공복
        - 비타민 C: 아침 식후
        - 비타민 A: 점심 식후
        - 비타민 D: 저녁 식후
        - 비타민 E: 저녁 식후
        - 비타민 K: 저녁 식후
        - 마그네슘: 저녁 식후, 자기 전
        - 칼슘: 저녁 식후
        - 오메가3: 점심 식후
        - 루테인: 아침 식후
        - 철분제: 아침 공복
        - 유산균: 아침 공복, 자기 전
        - 홍삼: 아침 공복
        - 단백질: 아침 식후
        - 레시틴: 아침 식후
        """

        response = openai.chat.completions.create(
            model=FINE_TUNED_MODEL_ID,
            messages=[
                {"role": "system", "content": "당신은 영양성분에 따라 영양제 복용 시간을 추천하는 전문가입니다."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=100
        )

        llm_response = response.choices[0].message.content.strip()  # 🔹 LLM의 전체 응답 저장

        # 4. LLM 응답에서 시간대(`optimal_timing`)만 추출
        match = re.search(r'(새벽|아침 공복|아침 식후|점심 공복|점심 식후|저녁 공복|저녁 식후|자기 전)', llm_response)
        optimal_timing = match.group(1) if match else "알 수 없음"  # 🔹 시간대가 없으면 "알 수 없음"

        # 5. 기존 `advice` 형식 유지
        advice = f"{main_ingredient}은(는) {optimal_timing}에 복용하는 것이 가장 좋아요!"

        # 6. 섭취 시간 데이터 변환
        optimal_time_formatted = extract_time(optimal_timing)

        # 7. DB에 데이터 저장
        insert_query = """
        INSERT INTO recommended_intake_time (created_at, updated_at, advice, recommended_time, user_id, user_supplement_id)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        created_at = datetime.now()
        updated_at = created_at

        cur.execute(insert_query,
                    (created_at, updated_at, advice, optimal_time_formatted, user_id,
                     supplement_id))
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({
            "advice": advice,
            "optimalTimeFormatted": optimal_time_formatted
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500