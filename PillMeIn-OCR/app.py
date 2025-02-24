from flask import Flask, request, jsonify
from ocr import extractTextWithGoogleVision
from gpt_summary import summarizeSupplementInfo
from flasgger import Swagger, swag_from

app = Flask(__name__)
swagger = Swagger(app)

@app.route('/upload', methods=['POST'])
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
            'allowMultiple': True  # 🔹 여러 개의 파일 선택 가능하도록 설정
        }
    ],
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
        400: {'description': '잘못된 요청 (이미지가 없거나 잘못됨)'},
        500: {'description': '서버 오류 (OCR 또는 AI 문제)'}
    }
})

def uploadImages():
    """사용자가 이미지를 업로드하면 OCR → GPT 분석 → JSON 반환"""
    if 'images' not in request.files:
        return jsonify({"error": "이미지를 업로드해주세요."}), 400

    imageFiles = request.files.getlist('images')  # 여러 이미지 처리
    if not imageFiles:
        return jsonify({"error": "이미지가 없습니다."}), 400

    # OCR 수행
    scannedTextList = extractTextWithGoogleVision(imageFiles)
    if isinstance(scannedTextList, str) and scannedTextList.startswith("Error"):
        return jsonify({"error": scannedTextList}), 500

    # GPT 요약 수행
    summary = summarizeSupplementInfo(scannedTextList)

    return jsonify(summary)  # 🔹 수정된 응답 형식 적용


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)