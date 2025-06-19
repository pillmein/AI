## Source code에 대한 설명
### 폴더 구조

```
📂 Finetuning-SupplementRecommendation
├── qa_data.py (PubMed API로 지정된 키워드를 통해 qa data 생성)
├── dataset.jsonl (생성된 qa data)
├── finetuning.py (파인튜닝 실행 코드)
├── test.py (파인튜닝 진행 상황 확인 코드)
├── generate_embeddings.py
📂 Finetuning-SupplementRecommendation
├── qa_data.py (PubMed API로 지정된 키워드를 통해 qa data 생성)
├── dataset.jsonl (생성된 qa data)
├── finetuning.py (파인튜닝 실행 코드)
├── check_status.py (파인튜닝 진행 상황 확인 코드)
├── index.pkl
.gitignore
Dockerfile
api_analysis.py ([POST] /save_analysis 영양제 정보 분석 결과 DB에 저장, [DELETE] /delete_analysis DB의 영양제 정보 분석 결과 삭제、 [GET] /get_supplements DB의 저장된 영양제 목록 불러오기、[GET] /get_supplement/ DB의 저장된 영양제 중 특정 영양제의 상세 정보 불러오기)
api_favorites.py ([POST] /save_favorite 찜한 영양제 DB에 저장、[GET] /get_favorite DB의 찜한 영양제 목록 불러오기、[DELETE] /delete_favorite DB의 찜한 영양제 삭제、[GET] /get_favorite/<api_supplement_id> DB의 찜한 영양제 중 특정 영양제의 상세 정보 불러오기）
api_health_probelm.py （[POST] /health-analysis 사용자의 건강 문제 분석）
api_ocr_analyze.py ([POST] /analyze OCR 스캔과 LLM 모델을 통해 영양제 정보 분석 결과 제공)
api_sup_recommendation.py ([POST] /recommend 유저 ID를 기반으로 건강 문제를 분석하고 3가지 영양제 추천)
api_time_recommendation.py （[POST] /supplement-timing 영양성분을 섭취하기 좋은 시간 추천）
config.py
dbconnect.py
embeddings.py
gpt_sup_recommendation.py
index.pkl
main.py
naver_shopping_service.py
ocr.py
ocr_gpt_summary.py
requirements.py
supervisord.conf
```

<br>

### 빌드 방식
Ｄｏｃｋｅｒｆｉｌｅ
작업 디렉토리 설정、 필요한 파일 복사、 패키지 설치、 Ｆｌａｓｋ 실행

---

### How to Install

<br>
1. Repository 클론
<br><br>

```
git clone https://github.com/pillmein/AI.git
cd AI
```

 <br>
２. 로컬 환경에서 테스트
<br><br>

```
ｐｙｔｈｏｎ ｍａｉｎ。ｐｙ
```
<br>

### How to Test

#### 주의
.gitignore에 포함된 .env 와 ornate-reef-462707-m5-2dbd8371d12f.json 파일이 있어야 정상 실행 가능합니다.

<br>
로컬 환경에서 테스트
<br><br>

```
config.py에서 DB_CONFIG 내용을 로컬 DB 정보(host, port, database, user, password)로 변경
main.py 실행 후 http://127.0.0.1:5000/apidocs/ 에서 API 실행 테스트 가능 ('Bearer+토큰'으로 인증 필요)
```

---

## Open Source

### AI Libraries & Tools

1. **Flask**: [Flask 공식 사이트](https://flask.palletsprojects.com/en/stable/)

２. **OpenAI API** – [OpenAI 공식 사이트](https://platform.openai.com/)  
   GPT 모델을 통해 건강 분석, 영양제 추천, OCR 분석 요약 등에 사용

３. **Google Cloud Vision API** – [Google Cloud Vision 공식 사이트](https://cloud.google.com/vision)  
   영양제 이미지에서 텍스트를 추출하는 OCR 기능에 활용

４. **Naver Shopping API** – [Naver Developers 공식 사이트](https://developers.naver.com/docs/search/shopping/)  
   영양제 정보를 검색하거나 상세 데이터를 가져오기 위해 사용

５. **FAISS** – [FAISS 공식 사이트](https://github.com/facebookresearch/faiss)  
   임베딩 기반 유사도 검색을 위해 사용

６. **Transformers (Hugging Face)** – [Transformers 공식 사이트](https://huggingface.co/transformers/)  
   사전 학습 모델과 토크나이저를 통해 파인튜닝 및 임베딩 생성을 수행

７. **Tiktoken** – [tiktoken GitHub](https://github.com/openai/tiktoken)  
   OpenAI 모델의 입력 길이를 정확히 계산하는 데 사용

８. **Docker**: [Docker 공식 사이트](https://www.docker.com/)
   컨테이너 기반의 환경 설정 및 배포를 위한 플랫폼으로, 이 프로젝트의 배포 및 실행 환경 구성

９. **PubMed API**: [PubMed 공식 사이트](https://www.ncbi.nlm.nih.gov/books/NBK25501/)
   논문 검색 및 데이터 수집
