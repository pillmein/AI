from flask import Flask, request, jsonify
import psycopg2
import jwt
import re
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

@app.route('/save_favorite', methods=['POST'])
@swag_from({
    'tags': ['Favorites'],
    'summary': '찜한 영양제 추가',
    'parameters': [
        {'name': 'body', 'in': 'body', 'required': True, 'schema': {
            'type': 'object',
            'properties': {
                'userId': {'type': 'integer'},
                'apiSupplementId': {'type': 'integer'},
                'imgUrl': {'type': 'string'}
            }
        }}
    ],
    'responses': {
        201: {'description': '찜한 영양제 추가 성공'},
        400: {'description': '잘못된 요청입니다.'},
        401: {'description': '유효하지 않은 토큰입니다.'},
        500: {'description': '내부 서버 에러'}
    }
})
def save_favorite():
    data = request.get_json()
    if not data:
        return jsonify({"error": "잘못된 요청입니다."}), 400

    user_id = data.get("userId")
    api_supplement_id = data.get("apiSupplementId")
    img_url = data.get("imgUrl")
    created_at = updated_at = datetime.utcnow()

    if not user_id or not api_supplement_id or not img_url:
        return jsonify({"error": "모든 필드를 입력해야 합니다."}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        query = """
        INSERT INTO favorites (created_at, updated_at, user_id, api_supplement_id, img_url)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id;
        """
        cur.execute(query, (created_at, updated_at, user_id, api_supplement_id, img_url))
        result_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({"message": "찜한 영양제 추가 성공", "id": result_id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/delete_favorite', methods=['DELETE'])
@swag_from({
    'tags': ['Favorites'],
    'summary': '즐겨찾기 삭제',
    'parameters': [
        {'name': 'body', 'in': 'body', 'required': True, 'schema': {
            'type': 'object',
            'properties': {
                'userId': {'type': 'integer'},
                'apiSupplementId': {'type': 'integer'}
            }
        }}
    ],
    'responses': {
        200: {'description': '찜한 영양제 삭제 성공'},
        400: {'description': '잘못된 요청입니다.'},
        401: {'description': '유효하지 않은 토큰입니다.'},
        500: {'description': '내부 서버 에러'}
    }
})
def delete_favorite():
    data = request.get_json()
    if not data:
        return jsonify({"error": "잘못된 요청입니다."}), 400

    user_id = data.get("userId")
    api_supplement_id = data.get("apiSupplementId")

    if not user_id or not api_supplement_id:
        return jsonify({"error": "모든 필드를 입력해야 합니다."}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        query = """
        DELETE FROM favorites WHERE user_id = %s AND api_supplement_id = %s;
        """
        cur.execute(query, (user_id, api_supplement_id))
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({"message": "찜한 영양제 삭제 성공"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/get_favorites', methods=['GET'])
@swag_from({
    'tags': ['Favorites'],
    'summary': '즐겨찾기 목록 조회',
    'parameters': [
        {'name': 'userId', 'in': 'query', 'type': 'integer', 'required': True, 'description': '사용자 ID'}
    ],
    'responses': {
        200: {'description': '즐겨찾기 목록 반환'},
        400: {'description': '잘못된 요청입니다.'},
        401: {'description': '유효하지 않은 토큰입니다.'},
        500: {'description': '내부 서버 에러'}
    }
})
def get_favorites():
    user_id = request.args.get("userId")
    if not user_id:
        return jsonify({"error": "userId가 필요합니다."}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        query = """
        SELECT f.api_supplement_id, f.img_url, a.name, a.effects, a.ingredients, a.warnings 
        FROM favorites f 
        JOIN api_supplements a ON f.api_supplement_id = a.id 
        WHERE f.user_id = %s;
        """
        cur.execute(query, (user_id,))
        favorites = cur.fetchall()

        cur.close()
        conn.close()

        results = [
            {"apiSupplementId": row[0], "imgUrl": row[1], "name": row[2], "effects": row[3], "ingredients": row[4],
             "warnings": row[5]}
            for row in favorites
        ]

        return jsonify(results), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/get_favorite/<int:api_supplement_id>', methods=['GET'])
@swag_from({
    'tags': ['Favorites'],
    'summary': '특정 영양제의 즐겨찾기 정보 조회',
    'parameters': [
        {
            'name': 'apiSupplementId',
            'in': 'path',
            'type': 'integer',
            'required': True,
            'description': '조회할 영양제의 ID'
        }
    ],
    'responses': {
        200: {
            'description': '영양제 정보 반환',
            'schema': {
                'type': 'object',
                'properties': {
                    'name': {'type': 'string'},
                    'ingredients': {'type': 'array', 'items': {'type': 'string'}},
                    'effects': {'type': 'array', 'items': {'type': 'string'}},
                    'warnings': {'type': 'array', 'items': {'type': 'string'}}
                }
            }
        },
        400: {'description': '잘못된 요청입니다.'},
        404: {'description': '해당 ID의 영양제를 찾을 수 없습니다.'},
        500: {'description': '내부 서버 에러'}
    }
})
def get_favorite(api_supplement_id):
    """특정 영양제 ID를 받아 즐겨찾기된 영양제 정보를 조회하는 API"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # ✅ 특정 영양제의 정보 조회
        query = """
        SELECT name, ingredients, effects, warnings 
        FROM api_supplements
        WHERE id = %s;
        """
        cur.execute(query, (api_supplement_id,))
        result = cur.fetchone()

        cur.close()
        conn.close()

        if not result:
            return jsonify({"error": "해당 ID의 영양제를 찾을 수 없습니다."}), 404

        # ✅ 데이터 가공 함수
        def split_ingredients(value):
            """괄호 안의 내용을 삭제한 후, 괄호 밖의 콤마 기준으로 리스트 변환"""
            if not value:
                return []

            # Step 1: 괄호 안의 내용 삭제
            value = re.sub(r'\([^)]*\)', '', value)
            # Step 2: 콤마 기준으로 나누고 공백 제거
            return [item.strip() for item in value.split(',') if item.strip()]

        def split_by_numbers(value):
            """①, ②, ③ 같은 번호 기준으로 리스트 변환"""
            return re.split(r'①|②|③|④|⑤|⑥|⑦|⑧|⑨|⑩', value)[1:] if value else []

        def split_warnings(value):
            """\n을 기준으로 분리하되, \r\n이 포함된 경우에도 \n을 기준으로 나누고 \r 제거"""
            if not value:
                return []
            # '\n' 기준으로 먼저 분리
            parts = [part.strip().replace("\r", "") for part in value.split("\n") if part.strip()]
            return parts

        # ✅ 문자열을 리스트로 변환
        supplement_info = {
            "name": result[0],
            "ingredients": split_ingredients(result[1]),  # 괄호 안의 콤마 유지하면서 리스트 변환
            "effects": split_by_numbers(result[2]),  # ①, ②, ③ 기준 분리
            "warnings": split_warnings(result[3])  # '\n' 기준으로 분리 + \r 제거
        }

        return jsonify(supplement_info), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500



if __name__ == '__main__':
    print("✅ Flask 서버 시작 중...")
    app.run(host='0.0.0.0', port=5000, debug=True)