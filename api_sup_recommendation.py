from flask import Flask, request, jsonify, Blueprint
from flasgger import Swagger
import openai
from flasgger import swag_from
from sentence_transformers import SentenceTransformer
from config import OPENAI_API_KEY, SECRET_KEY
from dbconnect import get_user_survey, get_supplement_id_by_name
from gpt_sup_recommendation import rag_qa_system, load_data, generate_health_summary
from naver_shopping_service import NaverShoppingService
from flask_jwt_extended import JWTManager, get_jwt_identity, jwt_required

# OpenAI API 키 설정
openai.api_key = OPENAI_API_KEY
# SentenceTransformer 전역변수 선언
model_name = 'sentence-transformers/all-MiniLM-L6-v2'
embedder = SentenceTransformer(model_name)
# 서버 실행 전에 데이터 로드
df_items, index = load_data()
# 네이버 쇼핑 서비스 인스턴스 생성
naver_service = NaverShoppingService()
# 🔥 index가 None이면 에러 발생하도록 확인
if df_items is None or index is None:
    raise RuntimeError("❌ 데이터 로드 실패! load_data() 결과를 확인하세요.")

# Flask 인스턴스 생성
blueprint = Blueprint('sup_recommendation_api', __name__)

# ✅ Swagger에서 Access Token 입력 필드 추가
swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "OCR & Supplement Analysis API",
        "description": "Google Vision을 사용한 OCR 및 GPT를 활용한 영양제 분석 API",
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



@blueprint.route("/recommend", methods=["POST"])
@jwt_required()
@swag_from({
    'tags': ['Supplement Recommendation'],
    'summary': '유저 건강 데이터를 기반으로 3가지 영양제를 추천합니다.',
    'security': [{"Bearer": []}],  # ✅ API 호출 시 Access Token 필수
    'responses': {
        200: {
            'description': '추천된 영양제 리스트',
            'schema': {
                'type': 'object',
                'properties': {
                    'userId': {'type': 'integer'},
                    'recSupplement1': {'type': 'object'},
                    'recSupplement2': {'type': 'object'},
                    'recSupplement3': {'type': 'object'}
                }
            }
        },
        400: {'description': '잘못된 요청입니다. (userId 없음)'},
        401: {'description': '유효하지 않은 토큰입니다.'},
        500: {'description': '내부 서버 에러'}
    }
})
def recommend_supplements():
    """사용자 건강 데이터를 기반으로 3가지 영양제 추천"""
    user_id = get_jwt_identity()
    if not user_id:
        return jsonify({"error": "userId가 필요합니다."}), 400

    # 1. 유저 설문 결과 가져오기
    survey_data = get_user_survey(user_id)
    if not survey_data:
        return jsonify({"error": "설문 데이터를 찾을 수 없습니다."}), 404

    # 2. 건강 문제 요약
    health_summary = generate_health_summary(survey_data)
    print(health_summary)
    question = f"""
    사용자의 주요 건강 문제는 다음과 같습니다: {health_summary}.
    이 중 가장 우선순위가 높은 건강 문제 3가지에 대해 각각 효과적인 영양제를 하나씩 추천해 주세요.

    - 총 3개의 서로 다른 영양제를 추천해야 합니다.
    - 각 영양제는 이름, 주요 성분, 기대 효과, 해결하고자 하는 건강 문제를 포함해야 합니다.
    - 같은 영양제를 여러 건강 문제에 중복 추천하지 마세요.
    """

    # 3. 추천 영양제 생성
    recommendation = rag_qa_system(question, df_items, index, user_id)

    # 4. 포맷 정리
    rec_lines = recommendation.split("\n")
    recs = []
    current_rec = {}

    for line in rec_lines:
        if line.startswith("1. 건강 문제") or line.startswith("2. 건강 문제") or line.startswith("3. 건강 문제"):
            if current_rec:
                recs.append(current_rec)
            current_rec = {"healthIssue": line.split(": ")[1]}
        elif "추천 영양제" in line:
            current_rec["name"] = line.split(": ")[1]
        elif "주요 원재료" in line:
            current_rec["ingredients"] = line.split(": ")[1]
        elif "효과" in line:
            current_rec["effect"] = line.split(": ")[1]
    if current_rec:
        recs.append(current_rec)

    # 5. 네이버 쇼핑 API를 사용하여 각 영양제의 이미지 URL 추가
    for rec in recs:
        supplement_name = rec.get("name")
        if supplement_name:
            image_url = naver_service.search_image_url(supplement_name)
            rec["imageUrl"] = image_url if image_url else "이미지 없음"
            supplement_id = get_supplement_id_by_name(supplement_name)
            rec["apiSupplementId"] = supplement_id if supplement_id is not None else -1  # -1로 에러 표시

    # 6. 결과 반환
    if len(recs) != 3:
        return jsonify({"error": "추천 영양제 파싱 오류"}), 500

    return jsonify({
        "userId": user_id,
        "recSupplement1": recs[0],
        "recSupplement2": recs[1],
        "recSupplement3": recs[2]
    })