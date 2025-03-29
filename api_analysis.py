from flask import Flask, request, jsonify
import psycopg2
from flasgger import Swagger, swag_from
from datetime import datetime
from config import SECRET_KEY, DB_CONFIG
from flask_jwt_extended import JWTManager, get_jwt_identity, jwt_required

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

app = Flask(__name__)

app.config["JWT_SECRET_KEY"] = SECRET_KEY
jwt = JWTManager(app)

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



@app.route('/save_analysis', methods=['POST'])
@jwt_required()
@swag_from({
    'tags': ['Supplement Analysis'],
    'summary': 'OCR 분석 결과를 DB에 저장',
    'security': [{"Bearer": []}],  # ✅ Swagger에 토큰 필수 설정
    'parameters': [
        {'name': 'body', 'in': 'body', 'required': True, 'schema': {
            'type': 'object',
            'properties': {
                'name': {'type': 'string'},
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
    data = request.get_json()
    if not data:
        return jsonify({"error": "잘못된 요청입니다."}), 400

    user_id = get_jwt_identity()
    name = data.get("name")
    if not user_id or not name:
        return jsonify({"error": "userId와 name이 필요합니다."}), 400

    ingredients = ", ".join(data.get("mainIngredients", []))
    effects = ", ".join(data.get("effects", []))
    warnings = ", ".join(data.get("precautions", []))
    for_who = ", ".join(data.get("whoNeedsThis", []))
    created_at = updated_at = datetime.utcnow()

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        query = """
        INSERT INTO analyzed_supplements (created_at, updated_at, user_id, name, ingredients, effects, warnings, for_who)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id;
        """
        cur.execute(query, (created_at, updated_at, user_id, name, ingredients, effects, warnings, for_who))
        result_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({"message": "저장 성공", "id": result_id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500



@app.route('/delete_analysis', methods=['DELETE'])
@jwt_required()
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



@app.route('/get_supplements', methods=['GET'])
@jwt_required()
@swag_from({
    'tags': ['Supplement Analysis'],
    'summary': '사용자가 저장한 영양제 목록을 가져옵니다.',
    'security': [{"Bearer": []}],  # ✅ API 호출 시 JWT 인증 필요
    'responses': {
        200: {
            'description': '사용자가 저장한 영양제 목록',
            'schema': {
                'type': 'object',
                'properties': {
                    'supplements': {'type': 'array', 'items': {'type': 'string'}}
                }
            }
        },
        400: {'description': '잘못된 요청입니다. (userId 없음)'},
        401: {'description': '유효하지 않은 토큰입니다.'},
        500: {'description': '내부 서버 에러'}
    }
})
def get_supplements():
    """사용자가 저장한 영양제 이름 목록을 가져오는 API (GET 방식)"""
    user_id = get_jwt_identity()
    if not user_id:
        return jsonify({"error": "userId가 필요합니다."}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # ✅ 특정 사용자의 영양제 이름 가져오기
        cur.execute("SELECT name FROM analyzed_supplements WHERE user_id = %s", (user_id,))
        supplements = [row[0] for row in cur.fetchall()]  # 리스트로 변환

        cur.close()
        conn.close()

        return jsonify({"supplements": supplements}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500



@app.route('/get_supplement/<int:supplement_id>', methods=['GET'])
@swag_from({
    'tags': ['Supplement Analysis'],
    'summary': '특정 ID의 영양제 정보를 조회합니다.',
    'parameters': [
        {
            'name': 'supplement_id',
            'in': 'path',
            'type': 'integer',
            'required': True,
            'description': '조회할 영양제의 ID'
        }
    ],
    'responses': {
        200: {
            'description': '영양제 정보 조회 성공',
            'schema': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'integer'},
                    'name': {'type': 'string'},
                    'effects': {'type': 'array', 'items': {'type': 'string'}},
                    'for_who': {'type': 'array', 'items': {'type': 'string'}},
                    'ingredients': {'type': 'array', 'items': {'type': 'string'}},
                    'warnings': {'type': 'array', 'items': {'type': 'string'}}
                }
            }
        },
        400: {'description': '잘못된 요청입니다.'},
        404: {'description': '해당 ID의 영양제를 찾을 수 없습니다.'},
        500: {'description': '내부 서버 에러'}
    }
})
def get_supplement(supplement_id):
    """특정 ID(PK)로 영양제 정보 조회 API"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # ✅ 특정 ID의 영양제 정보 가져오기
        query = """
        SELECT id, name, effects, for_who, ingredients, warnings
        FROM analyzed_supplements
        WHERE id = %s;
        """
        cur.execute(query, (supplement_id,))
        result = cur.fetchone()

        cur.close()
        conn.close()

        if not result:
            return jsonify({"error": "해당 ID의 영양제를 찾을 수 없습니다."}), 404

        # ✅ 문자열을 리스트로 변환 (콤마 기준)
        def split_to_list(value):
            return value.split(", ") if value else []

        supplement_info = {
            "id": result[0],
            "name": result[1],
            "effects": split_to_list(result[2]),
            "for_who": split_to_list(result[3]),
            "ingredients": split_to_list(result[4]),
            "warnings": split_to_list(result[5])
        }

        return jsonify(supplement_info), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    print("✅ Flask 서버 시작 중...")
    app.run(host='0.0.0.0', port=5000, debug=True)
