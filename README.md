# AI

[POST] /recommend
유저 ID를 기반으로 건강 문제를 분석하고 3가지 영양제 추천

[POST] /analyze
OCR 스캔과 LLM 모델을 통해 영양제 정보 분석 결과 제공

[POST] /save_analysis
영양제 정보 분석 결과 DB에 저장

[DELETE] /delete_analysis
DB의 영양제 정보 분석 결과 삭제

[POST] /save_favorite
찜한 영양제 DB에 저장

[GET] /get_favorite
DB의 찜한 영양제 목록 불러오기

[DELETE] /delete_favorite
DB의 찜한 영양제 삭제

[GET] /get_supplements
DB의 저장된 영양제 목록 불러오기

[GET] /get_supplement/<id>
DB의 저장된 영양제 중 특정 영양제의 상세 정보 불러오기

[GET] /get_favorite/<api_supplement_id>
DB의 찜한 영양제 중 특정 영양제의 상세 정보 불러오기

[POST] /supplement-timing
영양성분을 섭취하기 좋은 시간 추천

[POST] /health-analysis
사용자의 건강 문제 분석

##Docker 빌드 및 실행##
docker build -t multi-api .
docker run -d -p 5000:5000 -p 5001:5001 -p 5002:5002 -p 5003:5003 -p 5004:5004 -p 5005:5005 multi-api