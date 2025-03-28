import os
from google.cloud import vision
from google.cloud.vision_v1 import types
from config import GOOGLE_APPLICATION_CREDENTIALS

# Google Cloud 인증 키 설정
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GOOGLE_APPLICATION_CREDENTIALS

# Google Vision API 클라이언트 초기화
visionClient = vision.ImageAnnotatorClient()

def extractTextWithGoogleVision(imageFiles):
    """Google Vision API를 사용하여 OCR 수행"""
    allTexts = []

    for imageFile in imageFiles:
        content = imageFile.read()
        image = types.Image(content=content)
        response = visionClient.text_detection(image=image)

        if response.error.message:
            return f"Error: {response.error.message}"

        texts = response.text_annotations
        extractedText = texts[0].description if texts else ""

        # 여러 개의 이미지에서 텍스트를 줄 단위로 리스트에 추가
        allTexts.extend(extractedText.split("\n"))

    return allTexts