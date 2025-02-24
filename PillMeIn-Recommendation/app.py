from flask import Flask, request, jsonify
from flasgger import Swagger
import openai
import psycopg2
import pandas as pd
from config import OPENAI_API_KEY
from dbconnect import get_user_survey
from gpt_recommendation import rag_qa_system, load_data

# Flask 인스턴스 생성
app = Flask(__name__)
Swagger(app)

# OpenAI API 키 설정
openai.api_key = OPENAI_API_KEY


@app.route("/recommend", methods=["POST"])
def recommend_supplements():
    """
    유저 ID를 기반으로 건강 문제를 분석하고 3가지 영양제를 추천합니다.
    ---
    parameters:
      - name: user_id
        in: body
        required: true
        schema:
          type: object
          properties:
            user_id:
              type: integer
              example: 1
    responses:
      200:
        description: 추천된 영양제 리스트
        schema:
          type: object
          properties:
            user_id:
              type: integer
            recSupplier1:
              type: object
              properties:
                name:
                  type: string
                health_issue:
                  type: string
                ingredients:
                  type: string
                effect:
                  type: string
            recSupplier2:
              type: object
              properties:
                name:
                  type: string
                health_issue:
                  type: string
                ingredients:
                  type: string
                effect:
                  type: string
            recSupplier3:
              type: object
              properties:
                name:
                  type: string
                health_issue:
                  type: string
                ingredients:
                  type: string
                effect:
                  type: string
    """
    user_id = request.json.get("user_id")
    if not user_id:
        return jsonify({"error": "user_id가 필요합니다."}), 400

    # 1. 유저 설문 결과 가져오기
    survey_data = get_user_survey(user_id)
    if not survey_data:
        return jsonify({"error": "설문 데이터를 찾을 수 없습니다."}), 404

    # 2. 건강 문제 요약
    health_summary = ", ".join([entry["concern"] for entry in survey_data])
    question = f"사용자의 건강 문제는 {health_summary} 입니다. 이 사용자의 건강 문제 3가지에 각각 도움이 되는 영양제를 3가지 찾아줘."

    # 3. 추천 영양제 생성
    recommendation = rag_qa_system(question)

    # 4. 포맷 정리
    rec_lines = recommendation.split("\n")
    recs = []
    current_rec = {}
    for line in rec_lines:
        if line.startswith("1. 건강 문제") or line.startswith("2. 건강 문제") or line.startswith("3. 건강 문제"):
            if current_rec:
                recs.append(current_rec)
            current_rec = {"health_issue": line.split(": ")[1]}
        elif "추천 영양제" in line:
            current_rec["name"] = line.split(": ")[1]
        elif "주요 원재료" in line:
            current_rec["ingredients"] = line.split(": ")[1]
        elif "효과" in line:
            current_rec["effect"] = line.split(": ")[1]
    if current_rec:
        recs.append(current_rec)

    # 5. 결과 반환
    if len(recs) != 3:
        return jsonify({"error": "추천 영양제 파싱 오류"}), 500

    return jsonify({
        "user_id": user_id,
        "recSupplement1": recs[0],
        "recSupplement2": recs[1],
        "recSupplement3": recs[2]
    })

# 서버 실행 전에 데이터 로드
df_items, embedder, index = load_data()

if __name__ == "__main__":
    print("✅ Flask 서버 시작 중...")
    app.run(debug=True)