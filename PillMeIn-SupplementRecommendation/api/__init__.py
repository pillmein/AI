"""
This module initializes the API blueprint and namespaces.
"""

from flask import Blueprint
from flask_restx import Api

# Create a blueprint for the API
blueprint = Blueprint('api', __name__)

# Initialize the API with the blueprint
api = Api(
    blueprint, # 블루프린트에 API를 연결
    title="REST API", # API의 제목 설정
    cription="REST API for the application" # API에 대한 설명 설정
)

# Import and add namespaces
from .routes import ns as api_namespace # routes 모듈에서 API 네임스페이스를 가져옴
api.add_namespace(api_namespace) # 가져온 네임스페이스를 API에 추가
# 네임스페이스: 프로그래밍에서 이름을 분리하거나 그룹화하여 추돌을 방지하는 방법 - API의 특정 엔드포인트와 리소스들을 논리적으로 그룹화하여 관리(기능별로 모듈화)