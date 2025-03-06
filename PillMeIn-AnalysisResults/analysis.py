from flask import Flask, request, jsonify
import psycopg2
import jwt  # ✅ JWT 인증 추가
from flasgger import Swagger, swag_from
from datetime import datetime
from config import SECRET_KEY

# ✅ PostgreSQL 연결 설정
DB_CONFIG = {
    "host": "127.0.0.1",
    "dbname": "test",
    "user": "postgres",
    "password": "ummong1330",
    "port": "5432"
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

app = Flask(__name__)

# ✅ Swagger에서 Access Token 입력 필드 추가
swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "Supplement Analysis API",
        "description": "OCR 분석 결과를 DB에 저장하는 API",
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
        # ✅ "Bearer <TOKEN>" 형식이므로 "Bearer " 제거
        token = auth_header.split(" ")[1]

        # ✅ JWT 검증 (서명 확인)
        decoded_token = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return decoded_token, None  # 검증 성공 시 토큰 정보 반환

    except jwt.ExpiredSignatureError:
        return None, jsonify({"error": "토큰이 만료되었습니다."}), 401
    except jwt.InvalidTokenError:
        return None, jsonify({"error": "유효하지 않은 토큰입니다."}), 401

@app.route('/save_analysis', methods=['POST'])
@swag_from({
    'tags': ['Supplement Analysis'],
    'summary': 'OCR 분석 결과를 DB에 저장',
    'security': [{"Bearer": []}],  # ✅ Swagger에 토큰 필수 설정
    'parameters': [
        {'name': 'body', 'in': 'body', 'required': True, 'schema': {
            'type': 'object',
            'properties': {
                'userId': {'type': 'integer'},
                'mainIngredients': {'type': 'array', 'items': {'type': 'string'}},
                'effects': {'type': 'array', 'items': {'type': 'string'}},
                'precautions': {'type': 'array', 'items': {'type': 'string'}},
                'whoNeedsThis': {'type': 'array', 'items': {'type': 'string'}}
            }
        }}
    ],
    'responses': {
        201: {'description': '분석 결과 저장 성공'},
        400: {'description': '잘못된 요청입니다.'},
        401: {'description': '유효하지 않은 토큰입니다.'},
        500: {'description': '내부 서버 에러'}
    }
})
def save_analysis():
    """OCR 분석 결과를 DB에 저장"""
    # ✅ 액세스 토큰 검증
    token_data, error_response = verify_token()
    if error_response:
        return error_response  # 인증 실패 시 오류 반환

    data = request.get_json()
    if not data:
        return jsonify({"error": "잘못된 요청입니다."}), 400

    user_id = data.get("userId")
    if not user_id:
        return jsonify({"error": "userId가 필요합니다."}), 400

    ingredients = ", ".join(data.get("mainIngredients", []))
    effects = ", ".join(data.get("effects", []))
    warnings = ", ".join(data.get("precautions", []))
    for_who = ", ".join(data.get("whoNeedsThis", []))
    created_at = updated_at = datetime.utcnow()

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        query = """
        INSERT INTO analyzed_supplements (created_at, updated_at, user_id, ingredients, effects, warnings, for_who)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id;
        """
        cur.execute(query, (created_at, updated_at, user_id, ingredients, effects, warnings, for_who))
        result_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({"message": "저장 성공", "id": result_id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500



@app.route('/delete_analysis', methods=['DELETE'])
@swag_from({
    'tags': ['Supplement Analysis'],
    'summary': '특정 분석 데이터를 삭제',
    'security': [{"Bearer": []}],  # ✅ Access Token 필요
    'parameters': [
        {
            'name': 'id',
            'in': 'query',
            'required': True,
            'type': 'integer',
            'description': '삭제할 분석 데이터 ID'
        }
    ],
    'responses': {
        200: {'description': '삭제 성공'},
        400: {'description': '잘못된 요청입니다. (id 없음)'},
        401: {'description': '유효하지 않은 토큰입니다.'},
        404: {'description': '삭제할 데이터가 없습니다.'},
        500: {'description': '내부 서버 에러'}
    }
})
def delete_analysis():
    """특정 분석 데이터를 삭제"""
    # ✅ Access Token 검증
    token_data, error_response = verify_token()
    if error_response:
        return error_response  # 토큰이 유효하지 않으면 오류 반환

    # ✅ 요청에서 id 가져오기
    analysis_id = request.args.get("id", type=int)
    if not analysis_id:
        return jsonify({"error": "id가 필요합니다."}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # ✅ id가 존재하는지 확인
        cur.execute("SELECT COUNT(*) FROM analyzed_supplements WHERE id = %s", (analysis_id,))
        count = cur.fetchone()[0]

        if count == 0:
            return jsonify({"error": f"id={analysis_id}의 분석 데이터가 존재하지 않습니다."}), 404

        # ✅ 삭제 실행
        cur.execute("DELETE FROM analyzed_supplements WHERE id = %s", (analysis_id,))
        conn.commit()

        cur.close()
        conn.close()

        return jsonify({"message": f"id={analysis_id}의 분석 데이터를 삭제했습니다."}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    print("✅ Flask 서버 시작 중...")
    app.run(host='0.0.0.0', port=5000, debug=True)
