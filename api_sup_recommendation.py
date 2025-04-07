from flask import Flask, request, jsonify, Blueprint
from flasgger import Swagger
import openai
from flasgger import swag_from
from sentence_transformers import SentenceTransformer
from config import OPENAI_API_KEY, SECRET_KEY
from dbconnect import get_user_survey
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
    question = f"사용자의 건강 문제는 {health_summary} 입니다. 이 사용자의 1~3순위 건강 문제 3가지에 각각 도움이 되는 영양제를 3가지 찾아 추천하세요."

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

    # 6. 결과 반환
    if len(recs) != 3:
        return jsonify({"error": "추천 영양제 파싱 오류"}), 500

    return jsonify({
        "userId": user_id,
        "recSupplement1": recs[0],
        "recSupplement2": recs[1],
        "recSupplement3": recs[2]
    })