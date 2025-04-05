from flask import Flask, request, jsonify, Blueprint
from flasgger import Swagger
import openai
from flasgger import swag_from
from config import OPENAI_API_KEY, SECRET_KEY
from dbconnect import get_user_survey
from flask_jwt_extended import JWTManager, get_jwt_identity, jwt_required

# OpenAI API 설정
openai.api_key = OPENAI_API_KEY

# Flask 인스턴스 생성
blueprint = Blueprint('health_problem_api', __name__)

# ✅ Swagger에서 Access Token 입력 필드 추가
swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "Health Problem Analysis API",
        "description": "건강 설문 기반 사용자의 건강 문제 분석 API",
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


@blueprint.route("/health-analysis", methods=["POST"])
@jwt_required()
@swag_from({
    'tags': ['Health Analysis'],
    'summary': '사용자의 생활 패턴을 분석하고 필요한 영양소를 추천합니다.',
    'security': [{"Bearer": []}],
    'responses': {
        200: {
            'description': '건강 분석 결과 반환',
            'schema': {
                'type': 'object',
                'properties': {
                    'userId': {'type': 'integer'},
                    'analysisSummary': {'type': 'string'}
                }
            }
        },
        400: {'description': '잘못된 요청 (userId 없음)'},
        401: {'description': '유효하지 않은 토큰'},
        404: {'description': '사용자의 설문 데이터를 찾을 수 없음'},
        500: {'description': '서버 오류'}
    }
})
def health_analysis():
    """사용자의 건강 설문 데이터를 분석하고 필요한 영양소를 추천하는 API"""
    user_id = get_jwt_identity()
    if not user_id:
        return jsonify({"error": "userId가 필요합니다."}), 400

    # 1. 사용자의 설문 데이터 가져오기
    survey_data = get_user_survey(user_id)
    if not survey_data:
        return jsonify({"error": "설문 데이터를 찾을 수 없습니다."}), 404

    # 2. 설문 데이터를 기반으로 LLM 프롬프트 생성
    context = "\n".join([
        f"- 질문: {item['question']}\n  응답: {item['answer']}\n  우려사항: {item['concern']}\n  필요한 영양소: {', '.join(item['required_nutrients']) if isinstance(item['required_nutrients'], list) else item['required_nutrients']}"
        for item in survey_data
    ])

    prompt = f"""
    당신은 건강 전문가 AI입니다. 사용자의 설문 데이터를 기반으로 생활 패턴과 건강 상태를 분석하고, 적절한 영양소와 복용 시간을 추천하세요.

    사용자 설문 데이터:
    {context}

    🎯 예시:
    "햇빛을 많이 쬐지 못하는 생활패턴이네요! 비타민 D를 점심 식사와 함께 복용하는 것을 추천해요. 수면 부족을 겪고 있으므로, 마그네슘을 저녁에 섭취하면 신경 안정과 수면 개선에 도움이 될 수 있어요."

    심각도 기준:
    - 만성 질환 관련 문제는 높은 우선순위
    - 식습관이 매우 불균형할 경우 높은 우선순위
    - 특정 영양소 결핍 위험이 클 경우 높은 우선순위

    사용자가 '매우 자주 있음'이라고 응답한 문제가 가장 심각한 문제인 것으로 판단하고, 건강 데이터를 기반으로 우선순위를 결정하세요.
    이제 사용자의 건강 상태를 답변 형식에 맞게 1~3순위로 정리하고, 그 근거를 함께 제시하세요.

    🔹 지침:
    - **불필요한 서론 없이 바로 조언 시작**
    - **간결하고 자연스러운 문장 사용 (최대 4~5문장)**
    - **과도한 설명 배제, 실용적인 조언만 포함**
    - **반말이 아닌 친절한 존댓말 사용**
    """

    # 3. GPT API 호출
    response = openai.chat.completions.create(
        model="gpt-4",  # LLM 모델 사용
        messages=[
            {"role": "system", "content": "당신은 건강 문제 분석 및 영양소 추천 전문가입니다."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=500
    )

    llm_response = response.choices[0].message.content.strip()

    return jsonify({
        "userId": user_id,
        "analysisSummary": llm_response
    })