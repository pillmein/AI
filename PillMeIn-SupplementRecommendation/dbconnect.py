import psycopg2
import pandas as pd
import json

def get_user_survey(user_id):
    # PostgreSQL 연결 정보
    db_params = {
        "host": "127.0.0.1",
        "dbname": "test",
        "user": "postgres",
        "password": "ummong1330",
        "port": "5432"
    }

    # 컬럼과 question, concern, required_nutrients 매핑
    column_mapping = {
        "alcohol_frequency": {
            "question": "한 달 평균 음주 빈도는 어떻게 되나요?",
            "concern": "간 기능 저하, 비타민 B군 결핍, 산화 스트레스 증가",
            "required_nutrients": ["비타민 B군", "밀크시슬", "NAC"]
        },
        "brittle_nails_hair": {
            "question": "손톱이 부러지거나 머리카락이 약해진 것을 느낀 적이 있나요?",
            "concern": "영양 부족, 손톱과 머리카락 약화",
            "required_nutrients": ["비오틴", "비타민 E", "아연", "단백질"]
        },
        "caffeine_intake": {
            "question": "카페인을 얼마나 자주 섭취하나요?",
            "concern": "탈수, 피로, 피부 건조",
            "required_nutrients": ["비타민 B군", "마그네슘", "칼슘", "철분"]
        },
        "diet_method": {
            "question": "현재 다이어트 중이시라면, 어떤 방식으로 다이어트를 하고 있나요?",
            "concern": "영양 불균형, 에너지 부족, 체력 저하",
            "required_nutrients": {
                "식이제한형": ["미네랄", "단백질"],
                "단식이나 하루 한 끼 식사": ["단백질", "비타민 B군"],
                "운동 중심": ["단백질", "탄수화물"]
            }
        },
        "digestion_issues": {
            "question": "소화가 잘 안 되거나 속이 더부룩한 증상을 느낀 적이 있나요?",
            "concern": "소화 기능 저하, 위장 문제",
            "required_nutrients": ["프로바이오틱스", "식이섬유", "비타민 B군", "파파야 효소"]
        },
        "eye_fatigue": {
            "question": "평소 시력이 저하되거나 눈이 피로해진 적이 있나요?",
            "concern": "눈의 피로, 시력 저하, 안구 건조증",
            "required_nutrients": ["비타민 A", "오메가-3 지방산", "루테인", "비타민 C"]
        },
        "focus_memory_issues": {
            "question": "최근 집중력이 저하되거나 기억력이 저하되는 것을 느낀 적이 있나요?",
            "concern": "집중력 저하, 인지 기능 저하",
            "required_nutrients": ["비타민 B군", "오메가-3 지방산", "철분", "비타민 E"]
        },
        "headache_dizziness": {
            "question": "머리가 아프거나, 어지러움을 자주 느끼나요?",
            "concern": "빈혈, 저혈압, 탈수",
            "required_nutrients": ["철분", "비타민 C", "비타민 B군"]
        },
        "infection_frequency": {
            "question": "감기나 염증반응이 얼마나 자주 생기나요?",
            "concern": "면역력 저하",
            "required_nutrients": ["비타민 C", "아연", "셀레늄", "비타민 D"]
        },
        "meal_pattern": {
            "question": "평소 식사는 주로 어떤 방식으로 하나요?",
            "concern": "영양소 불균형, 혈당 스파이크",
            "required_nutrients": ["멀티비타민미네랄", "식이섬유"]
        },
        "mental_fatigue": {
            "question": "(정신적 피로) 최근 스트레스나 불안감을 강하게 느낀 적이 얼마나 자주 있었나요?",
            "concern": "스트레스로 인한 피로, 집중력 저하, 면역력 저하",
            "required_nutrients": ["비타민 C", "마그네슘", "아연", "비타민 B군"]
        },
        "outdoor_activity": {
            "question": "걷기, 달리기, 자전거 타기 등의 야외 활동 또는 근력 운동과 같은 심박수를 높이는 신체 활동을 얼마나 자주 하나요?",
            "concern": "신체 활동 부족으로 인한 체력 저하, 면역력 저하",
            "required_nutrients": ["비타민 D", "칼슘", "마그네슘", "오메가-3 지방산"]
        },
        "pain_frequency": {
            "question": "신체 특정 부위에 통증(근육통, 관절통, 염증 등)이 자주 있나요?",
            "concern": "근육통, 관절통, 만성 염증",
            "required_nutrients": ["오메가-3 지방산", "글루코사민", "비타민 D", "마그네슘"]
        },
        "physical_fatigue": {
            "question": "육체적 피로감을 얼마나 자주 느끼나요?",
            "concern": "만성 피로, 빈혈, 수면 문제",
            "required_nutrients": ["철분", "비타민 B군", "비타민 C", "마그네슘"]
        },
        "screen_time": {
            "question": "하루에 스마트폰과 컴퓨터를 평균 몇 시간 정도 사용하나요?",
            "concern": "피로, 눈 건강 문제",
            "required_nutrients": ["오메가-3 지방산", "비타민 A"]
        },
        "seasonal_discomfort": {
            "question": "계절 변화에 따라 손발이 차거나, 몸이 무거워지는 느낌이 있나요?",
            "concern": "혈액순환 문제, 비타민 D 결핍, 저체온증",
            "required_nutrients": ["비타민 D", "비타민 K", "오메가-3 지방산", "비타민 E"]
        },
        "sedentary_hours": {
            "question": "앉아서 보내는 시간이 하루에 몇 시간 정도인가요?",
            "concern": "근골격계 문제, 혈액순환 장애",
            "required_nutrients": ["비타민 K", "오메가-3 지방산"]
        },
        "skin_concern": {
            "question": "어떤 피부 고민이 있으신가요?",
            "concern": "피부 트러블, 아토피",
            "required_nutrients": {
                "피부 탄력, 보습": ["콜라겐", "비타민 C"],
                "여드름성": ["아연", "비타민 B"],
                "아토피": ["프로바이오틱스", "오메가-3 지방산"]
            }
        },
        "sleep_disruption": {
            "question": "수면 중 뒤척이거나 깨는 날이 있나요?",
            "concern": "수면 장애, 스트레스, 호르몬 문제",
            "required_nutrients": ["마그네슘", "멜라토닌", "비타민 B군", "오메가-3 지방산"]
        },
        "sleep_duration": {
            "question": "일일 수면 시간은 몇 시간 정도인가요?",
            "concern": "수면 부족으로 인한 면역력 저하, 피로감",
            "required_nutrients": ["마그네슘", "아연", "멜라토닌"]
        },
        "weight_change": {
            "question": "최근 체중 변화(증가 또는 감소)가 있나요?",
            "concern": "호르몬 불균형, 영양 불균형",
            "required_nutrients": ["단백질", "비타민 D", "칼슘"]
        }
    }

    # 답변 매핑
    answer_mapping = {
        "alcohol_frequency": {
            "NEVER": "전혀 마시지 않음",
            "MONTHLY_1_2": "월 1-2회",
            "WEEKLY_1_2": "주 1-2회 (월 4-8회)",
            "WEEKLY_3_PLUS": "주 3회 이상 (월 9회 이상)"
        },
        "brittle_nails_hair": {
            "NOT_APPLICABLE": "해당 사항 없음",
            "OCCASIONALLY": "가끔 있음",
            "OFTEN": "자주 있음",
            "VERY_OFTEN": "매우 자주 있음"
        },
        "caffeine_intake": {
            "NEVER": "섭취하지 않음",
            "WEEKLY_1_2": "주 1-2회",
            "WEEKLY_3_4": "주 3-4회",
            "DAILY_OR_MORE": "매일 1회 이상"
        },
        "diet_method": {
            "NOT_APPLICABLE": "해당 사항 없음",
            "DIET_RESTRICTION": "식이제한형",
            "FASTING": "단식이나 하루 한 끼 식사",
            "EXERCISE_BASED": "운동 중심"
        },
        "digestion_issues": {
            "NOT_APPLICABLE": "해당 사항 없음",
            "OCCASIONALLY": "가끔 있음",
            "OFTEN": "자주 있음",
            "VERY_OFTEN": "매우 자주 있음"
        },
        "eye_fatigue": {
            "NOT_APPLICABLE": "해당 사항 없음",
            "OCCASIONALLY": "가끔 있음",
            "OFTEN": "자주 있음",
            "VERY_OFTEN": "매우 자주 있음"
        },
        "focus_memory_issues": {
            "NOT_APPLICABLE": "해당 사항 없음",
            "OCCASIONALLY": "가끔 있음",
            "OFTEN": "자주 있음",
            "VERY_OFTEN": "매우 자주 있음"
        },
        "headache_dizziness": {
            "NOT_APPLICABLE": "해당 사항 없음",
            "OCCASIONALLY": "가끔 있음",
            "OFTEN": "자주 있음",
            "VERY_OFTEN": "매우 자주 있음"
        },
        "infection_frequency": {
            "NOT_APPLICABLE": "해당 사항 없음",
            "ONCE_OR_TWICE": "1년에 1-2번",
            "THREE_TO_FOUR": "1년에 3-4번",
            "FOUR_OR_MORE": "1년에 4번 이상"
        },
        "meal_pattern": {
            "THREE_MEALS": "하루 세 끼 규칙적으로 식사",
            "IRREGULAR": "하루 1-2끼 불규칙하게 식사",
            "SKIP_MEALS": "끼니를 거르고 간식으로 대체",
            "DELIVERY_OR_OUTSIDE": "배달 음식이나 외식으로 끼니 해결"
        },
        "mental_fatigue": {
            "NOT_APPLICABLE": "해당 사항 없음",
            "OCCASIONALLY": "가끔 있음",
            "OFTEN": "자주 있음",
            "VERY_OFTEN": "매우 자주 있음"
        },
        "outdoor_activity": {
            "DAILY": "매일",
            "WEEK_2_3": "주 2-3회",
            "WEEKLY": "주 1회",
            "RARELY": "거의 하지 않음"
        },
        "pain_frequency": {
            "NOT_APPLICABLE": "해당 사항 없음",
            "OCCASIONALLY": "가끔 있음",
            "OFTEN": "자주 있음",
            "VERY_OFTEN": "매우 자주 있음"
        },
        "physical_fatigue": {
            "NOT_APPLICABLE": "해당 사항 없음",
            "OCCASIONALLY": "가끔 있음",
            "OFTEN": "자주 있음",
            "VERY_OFTEN": "매우 자주 있음"
        },
        "screen_time": {
            "LESS_THAN_1": "1시간 미만",
            "ONE_TO_THREE": "1-3시간",
            "THREE_TO_FIVE": "3-5시간",
            "MORE_THAN_5": "5시간 이상"
        },
        "seasonal_discomfort": {
            "NOT_APPLICABLE": "해당 사항 없음",
            "OCCASIONALLY": "가끔 있음",
            "OFTEN": "자주 있음",
            "VERY_OFTEN": "매우 자주 있음"
        },
        "sedentary_hours": {
            "LESS_THAN_2": "2시간 미만",
            "TWO_TO_FOUR": "2-4시간",
            "FOUR_TO_EIGHT": "4-8시간",
            "MORE_THAN_EIGHT": "8시간 이상"
        },
        "skin_concern": {
            "NOT_APPLICABLE": "해당 사항 없음",
            "MOISTURE": "탄력 및 보습",
            "ACNE": "여드름성",
            "ATOPIC": "아토피",
            "HYPERPIGMENTATION": "색소침착"
        },
        "sleep_disruption": {
            "NOT_APPLICABLE": "해당 사항 없음",
            "OCCASIONALLY": "가끔 있음",
            "OFTEN": "자주 있음",
            "VERY_OFTEN": "매우 자주 있음"
        },
        "sleep_duration": {
            "LESS_THAN_4": "4시간 미만",
            "FOUR_TO_SIX": "4-6시간",
            "SIX_TO_EIGHT": "6-8시간",
            "MORE_THAN_EIGHT": "8시간 이상"
        },
        "weight_change": {
            "NOT_APPLICABLE": "해당 사항 없음",
            "SLIGHT_CHANGE": "가벼운 변화가 있음",
            "RAPID_CHANGE": "급격한 변화가 있음",
            "FREQUENT_CHANGE": "자주 있음"
        }
    }

    try:
        # 데이터베이스 연결
        conn = psycopg2.connect(
            host="127.0.0.1",
            port="5432",
            database="test",
            user="postgres",
            password="ummong1330"
        )
        cursor = conn.cursor()

        # 특정 user_id의 데이터만 조회
        query = "SELECT * FROM user_survey WHERE user_id = %s;"
        df = pd.read_sql(query, conn, params=[user_id])

        survey_data = []

        for _, row in df.iterrows():
            for col, meta in column_mapping.items():
                if col in row:
                    raw_answer = row[col]

                    # "NOT_APPLICABLE"이면 제외
                    if raw_answer == "NOT_APPLICABLE":
                        continue

                        # 매핑된 답변 값 찾기 (없으면 원본 값 사용)
                    mapped_answer = answer_mapping.get(col, {}).get(raw_answer, raw_answer)

                    # JSON 형식으로 데이터 추가
                    entry = {
                        "question": meta["question"],
                        "answer": mapped_answer,
                        "concern": meta["concern"],
                        "required_nutrients": meta["required_nutrients"]
                    }
                    survey_data.append(entry)

            health_purpose = row.get("health_purpose", "").strip()  # 공백 제거
            if health_purpose:  # 값이 있을 때만 추가
                survey_data.append({
                    "question": "영양제 섭취 목적",
                    "answer": health_purpose,
                    "concern": "사용자가 원하는 건강 목표",
                    "required_nutrients": []
                })

        # ✅ JSON 내용 리턴
        return survey_data

    except Exception as e:
        print(f"오류 발생: {e}")

    finally:
        if 'conn' in locals():
            cursor.close()
            conn.close()