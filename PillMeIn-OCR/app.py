from flask import Flask, request, jsonify
import jwt  # JWT 토큰 검증을 위한 라이브러리
from ocr import extractTextWithGoogleVision
from gpt_summary import summarizeSupplementInfo
from flasgger import Swagger, swag_from
from config import SECRET_KEY

app = Flask(__name__)

# ✅ Swagger 설정 (Authorization 헤더 추가)
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
        return None, jsonify({"error": "토큰이 만료되었습니다."}), 401
    except jwt.InvalidTokenError:
        return None, jsonify({"error": "유효하지 않은 토큰입니다."}), 401


@app.route('/analyze', methods=['POST'])
@swag_from({
    'tags': ['OCR & Supplement Analysis'],
    'summary': '이미지를 업로드하고 OCR 및 AI 분석을 수행합니다.',
    'consumes': ['multipart/form-data'],
    'parameters': [
        {
            'name': 'images',
            'in': 'formData',
            'type': 'file',
            'required': True,
            'description': 'OCR을 수행할 이미지 파일 (하나 이상의 이미지 가능)',
            'allowMultiple': True
        }
    ],
    'security': [{"Bearer": []}],  # ✅ API 호출 시 Access Token 필수
    'responses': {
        200: {
            'description': '분석된 영양제 정보',
            'schema': {
                'type': 'object',
                'properties': {
                    'majorIngredients': {'type': 'string', 'description': '주요 성분 및 함량'},
                    'effects': {'type': 'string', 'description': '영양제 효과'},
                    'precautions': {'type': 'string', 'description': '복용 시 주의사항'},
                    'recommendedFor': {'type': 'string', 'description': '누구에게 필요한지'}
                }
            }
        },
        400: {'description': '잘못된 요청입니다. (이미지가 없거나 잘못됨)'},
        401: {'description': '유효하지 않은 토큰입니다.'},
        500: {'description': '내부 서버 에러 (OCR 또는 AI 문제)'}
    }
})
def uploadImages():
    """사용자가 이미지를 업로드하면 OCR → GPT 분석 → JSON 반환"""
    # ✅ Access Token 검증
    token_data, error_response = verify_token()
    if error_response:
        return error_response  # 토큰이 유효하지 않으면 오류 반환

    if 'images' not in request.files:
        return jsonify({"error": "이미지를 업로드해주세요."}), 400

    imageFiles = request.files.getlist('images')
    if not imageFiles:
        return jsonify({"error": "이미지가 없습니다."}), 400

    # OCR 수행
    scannedTextList = extractTextWithGoogleVision(imageFiles)
    if isinstance(scannedTextList, str) and scannedTextList.startswith("Error"):
        return jsonify({"error": scannedTextList}), 500

    # GPT 요약 수행
    summary = summarizeSupplementInfo(scannedTextList)

    return jsonify(summary)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
