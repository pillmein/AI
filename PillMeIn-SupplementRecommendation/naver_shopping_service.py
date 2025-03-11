import requests
import os


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

        params = {"query": supplement_name}
        response = requests.get(self.BASE_URL, headers=headers, params=params)

        if response.status_code != 200:
            print(f"❌ 네이버 API 오류: {response.status_code}")
            return None

        data = response.json()
        items = data.get("items", [])

        if not items:
            return None  # 검색 결과 없음

        return items[0].get("image", None)  # 첫 번째 아이템의 이미지 URL 반환