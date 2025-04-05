import requests

class NaverShoppingService:
    BASE_URL = "https://openapi.naver.com/v1/search/shop.json"

    def __init__(self):
        self.client_id = "lsapUdiTcTYAW3WsU8EA"  # 환경 변수에서 API 키 가져오기
        self.client_secret = "af13L3OSOj"

    def search_image_url(self, supplement_name):
        headers = {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret,
            "Content-Type": "application/json"
        }

        query = f"{supplement_name} 영양제"
        params = {"query": query, "display": 5}
        response = requests.get(self.BASE_URL, headers=headers, params=params)

        if response.status_code != 200:
            print(f"❌ 네이버 API 오류: {response.status_code}")
            return None

        data = response.json()
        items = data.get("items", [])

        if not items:
            return None  # 검색 결과 없음

        # 🔍 키워드 정확도 필터링: 제목에 추천 제품명이 포함된 것 우선
        for item in items:
            title = item.get("title", "").replace("<b>", "").replace("</b>", "").lower()
            if supplement_name.lower() in title:
                return item.get("image")

        # 그렇지 않으면 첫 번째 이미지 fallback
        return items[0].get("image")