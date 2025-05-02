import openai
from config import OPENAI_API_KEY
import json

# OpenAI API 키 설정
openai.api_key = OPENAI_API_KEY

def summarizeSupplementInfo(scannedTextList):
    """GPT-3.5 Turbo를 사용하여 영양제 정보 요약"""
    scannedText = "\n".join(scannedTextList)

    prompt = f"""
    당신은 건강 보조제 전문가입니다. 사용자가 스캔한 영양제 라벨 정보를 제공합니다. 이를 바탕으로 다음과 같은 JSON 형식으로 정보를 요약하세요.

    스캔된 영양제 라벨 정보:
    {scannedText}

    반드시 다음과 같은 JSON 형식을 유지하세요:

    {{
        "mainIngredients": ["주요 성분 및 함량 (최대 3개)"],
        "effects": ["효과 (최대 3개)"],
        "precautions": ["복용 시 주의사항"],
        "whoNeedsThis": ["이 영양제가 필요한 사람"]
    }}

    📌 반드시 지켜야 할 규칙:
    -주요 성분은 가장 함량이 높은 3가지 성분만 제시하세요.
    -효과는 핵심 성분과 직접적으로 관련된 3가지만 포함하되, 각 영양소가 건강에 어떤 도움을 줄 수 있는지 이해하기 쉽게 구체적으로 설명하세요.
    -복용 시 주의사항은 복용 방법 및 이 영양제와 함께 섭취하면 안 되는 것들을 포함하세요.
    -영양제가 필요한 사람은 효과를 참고하여, 포함된 영양소가 구체적인 증상에 어떤 도움을 줄 수 있는지 포함하여 제시하세요.
    -JSON 형식이 유지되도록 답변을 생성하세요.
    """

    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an expert in summarizing supplement information based on scanned label data."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=800
    )
    # OpenAI 응답을 JSON 형식으로 파싱
    try:
        summary = json.loads(response.choices[0].message.content)
    except json.JSONDecodeError:
        summary = {
            "mainIngredients": [],
            "effects": [],
            "precautions": [],
            "whoNeedsThis": []
        }

    return summary