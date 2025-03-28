from flask import Flask, request, jsonify
from flasgger import Swagger
import openai
import jwt
from flasgger import swag_from
from config import OPENAI_API_KEY, SECRET_KEY
from dbconnect import get_user_survey

# OpenAI API 설정
openai.api_key = OPENAI_API_KEY

# Flask 인스턴스 생성
app = Flask(__name__)

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

swagger = Swagger(app, template=swagger_template)

def verify_token():
    """Access Token 검증 함수"""
    auth_header = request.headers.get("Authorization")

    if not auth_header:
        return None, jsonify({"error": "Authorization 헤더가 필요합니다."}), 401

    try:
        # ✅ "Bearer <TOKEN>" 형식으로 전송되므로, "Bearer " 제거
        token = auth_header.split(" ")[1]

        # ✅ JWT 검증 (토큰 서명 확인)
        decoded_token = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return decoded_token, None  # 검증 성공 시 토큰 정보 반환

    except jwt.ExpiredSignatureError:
        return None, jsonify({"error": "토큰이 만료되었습니다."})
    except jwt.InvalidTokenError:
        return None, jsonify({"error": "유효하지 않은 토큰입니다."})

def verify_token():
    """Access Token 검증 함수"""
    auth_header = request.headers.get("Authorization")

    if not auth_header:
        return None, jsonify({"error": "Authorization 헤더가 필요합니다."}), 401

    try:
        token = auth_header.split(" ")[1]  # "Bearer <TOKEN>"에서 "Bearer " 제거
        decoded_token = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return decoded_token, None
    except jwt.ExpiredSignatureError:
        return None, jsonify({"error": "토큰이 만료되었습니다."}), 401
    except jwt.InvalidTokenError:
        return None, jsonify({"error": "유효하지 않은 토큰입니다."}), 401

@app.route("/health-analysis", methods=["POST"])
@swag_from({
    'tags': ['Health Analysis'],
    'summary': '사용자의 생활 패턴을 분석하고 필요한 영양소를 추천합니다.',
    'security': [{"Bearer": []}],
    'parameters': [
        {
            'name': 'userId',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'userId': {'type': 'integer', 'example': 1}
                }
            }
        }
    ],
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
    # ✅ Access Token 검증
    token_data, error_response = verify_token()
    if error_response:
        return error_response  # 인증 실패 시 오류 반환

    user_id = request.json.get("userId")
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
            {"role": "system", "content": "당신은 건강 전문가입니다."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=400
    )

    llm_response = response.choices[0].message.content.strip()

    return jsonify({
        "userId": user_id,
        "analysisSummary": llm_response
    })

if __name__ == "__main__":
    print("✅ Flask 서버 시작 중...")
    app.run(debug=True)
