import requests
import time
import xml.etree.ElementTree as ET
import json
from datetime import datetime, timedelta

# PubMed API 키 (필요하면 설정)
PUBMED_API_KEY = "2dd265c0dd21aec9aaa877f6570f6799ea09"

# 설문 데이터 기반 검색 키워드
survey_keywords = [
    "physical activity AND immune function",
    "sedentary lifestyle AND musculoskeletal disorders",
    "sleep duration AND immune function",
    "screen time AND eye health",
    "caffeine consumption AND hydration",
    "irregular meals AND metabolic health",
    "alcohol consumption AND liver function",
    "chronic fatigue AND micronutrient deficiency",
    "stress AND immune function",
    "digestive issues AND probiotics",
    "headaches AND micronutrient deficiency",
    "frequent colds AND immune function",
    "skin elasticity AND collagen",
    "sudden weight change AND hormonal imbalance",
    "dieting AND nutritional deficiency",
    "sleep disturbances AND melatonin",
    "cold hands and feet AND circulation",
    "vision problems AND vitamin A",
    "joint pain AND omega-3",
    "memory decline AND vitamin B",
    "brittle nails and hair loss AND biotin"
]

# PubMed에서 논문 검색하는 함수 (설문 기반)
def search_pubmed(survey_keywords, pubmed_api_key):
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    articles = []
    collected_article_ids = set()

    # 최근 5년간 논문 검색
    start_date = (datetime.now() - timedelta(days=5*365)).strftime('%Y/%m/%d')

    for keyword in survey_keywords:
        search_url = f"{base_url}/esearch.fcgi"
        params = {
            "db": "pubmed",
            "term": keyword,
            "retmax": 5,  # 검색 결과 최대 개수
            "api_key": pubmed_api_key,
            "retmode": "json",
            "mindate": start_date,
            "datetype": "pdat"
        }

        response = requests.get(search_url, params=params)
        time.sleep(0.5)

        if response.status_code != 200:
            continue

        data = response.json()
        article_ids = data["esearchresult"]["idlist"]

        unique_article_ids = [aid for aid in article_ids if aid not in collected_article_ids]
        collected_article_ids.update(unique_article_ids)

        if unique_article_ids:
            fetch_url = f"{base_url}/efetch.fcgi"
            params = {
                "db": "pubmed",
                "id": ",".join(unique_article_ids),
                "retmode": "xml"
            }

            response = requests.get(fetch_url, params=params)
            time.sleep(0.5)

            if response.status_code == 200:
                root = ET.fromstring(response.content)
                for article in root.findall(".//PubmedArticle"):
                    title_elem = article.find(".//ArticleTitle")
                    abstract_elem = article.find(".//AbstractText")

                    title = title_elem.text.strip() if title_elem is not None and title_elem.text else ""
                    abstract = abstract_elem.text.strip() if abstract_elem is not None and abstract_elem.text else ""

                    if title and abstract:
                        articles.append({
                            "title": title,
                            "abstract": abstract
                        })

    return articles

# 논문 제목을 기반으로 질문 생성
def generate_question_from_article(title):
    """
    논문 제목을 기반으로 질문을 생성하는 함수
    """
    return f"{title}에 대한 연구 결과는 무엇인가요?"

# 논문 데이터를 QA 데이터셋으로 변환
def convert_articles_to_qa(articles):
    """
    PubMed에서 가져온 논문 리스트를 질문-응답 데이터셋으로 변환
    """
    qa_data = []

    for article in articles:
        title = article["title"]
        abstract = article["abstract"]
        question = generate_question_from_article(title)

        qa_data.append({
            "messages": [
                {"role": "system", "content": "당신은 건강 전문가입니다."},
                {"role": "user", "content": question},
                {"role": "assistant", "content": abstract}  # 논문의 초록을 답변으로 사용
            ]
        })

    return qa_data

# 실행
if __name__ == "__main__":
    articles = search_pubmed(survey_keywords, PUBMED_API_KEY)

    if articles:
        qa_data = convert_articles_to_qa(articles)
        with open("dataset.jsonl", "w", encoding="utf-8") as f:
            for item in qa_data:
                json.dump(item, f, ensure_ascii=False)
                f.write("\n")

        print(f"✅ {len(qa_data)}개의 질문-응답 데이터가 dataset.jsonl 파일에 저장되었습니다!")
    else:
        print("❌ 논문을 찾을 수 없습니다.")