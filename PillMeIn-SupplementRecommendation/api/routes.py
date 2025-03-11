"""
This module defines the API routes and resources.
"""

from flask import request, jsonify, current_app
from flask_restx import Namespace, Resource, fields
from models import db, KospiStockDaily, KospiStockSymbol, KospiValue
from analysis import corr, topNcorr

ns = Namespace('api', description='API operations') # 네임스페이스 생성, api 관련 작업들을 이 네임스페이스에 그룹화
user_model = ns.model('User', { # username과 emial 필드가 있는 User 모델 정의 - API 요청에서 필요한 데이터 구조 정의
    'username': fields.String(required=True, description='The user username'),
    'email': fields.String(required=True, description='The user email'),
})

@ns.route('/kospi_daily') # 클래스와 메서드를 특정 URL 경로에 매핑. 이 경로로 들어오는 HTTP 요청은 아래 정의된 리소스 클래스가 처리
class KospiDailyResource(Resource): # /kospi_daily 경로에 대한 요청을 처리하는 리소스 클래스. Resource를 상속받아 HTTP 메서드 정의 가능
    @ns.doc('list_kospi_daily') # 문서화 메타데이터 추가. list_kospi_daily라는 이름으로 엔드포인트 문서화
    def get(self): # /kospi_daily 경로로 들어오는 GET 요청 처리
        """List KOSPI daily data"""
        try:
            kospi_data = current_app.sess_presto.query(KospiStockDaily).limit(10).all() # Presto 데이터베이스 세션을 통해 'KospiStockDaily' 테이블에서 데이터 조회 (최대 10개까지 결과 리스트로 반환)

            return jsonify([{ # 조회된 kospi_data 리스트에서 각 항목을 JSON 형식으로 변환
                'symbol': data.symbol,
                'date': data.date,
                'price': data.price,
                'volume': data.volume,
                'value': data.value
            } for data in kospi_data])
        except Exception as e:
            return jsonify({'error': str(e)}), 500 # 에러 메시지를 포함한 JSON 응답 반환. HTTP 상태 코드: 500
        finally:
            current_app.sess_presto.close() # Presto 데이터베이스 세션 종료, 자원 해제

# 상관계수
@ns.route('/kospi_correlation/<string:symbol>/<int:start_date>/<int:end_date>') # 클래스와 메서드를 특정 URL 경로에 매핑. 이 경로로 들어오는 HTTP 요청은 아래 정의된 리소스 클래스가 처리
class KospiCorrelation(Resource): # /kospi_correlation 경로에 대한 요청을 처리하는 리소스 클래스. Resource를 상속받아 HTTP 메서드 정의 가능
    @ns.doc('list_kospi_correlation') # 문서화 메타데이터 추가. list_kospi_correlation라는 이름으로 엔드포인트 문서화
    def get(self, symbol, start_date, end_date): # /kospi_correlation 경로로 들어오는 GET 요청 처리
        """List KOSPI daily data"""
        try:
            res_dict = corr(current_app, symbol, start_date, end_date) # corr 함수 호출
            return jsonify(res_dict)
        except Exception as e:
            return jsonify({'error': str(e)}), 500 # 에러 메시지를 포함한 JSON 응답 반환. HTTP 상태 코드: 500
        finally:
            current_app.sess_presto.close() # Presto 데이터베이스 세션 종료, 자원 해제

# 종목 별 상관계수 계산해 상위 n개 출력
@ns.route('/kospi_topNcorr/<string:abs>/<int:start_date>/<int:end_date>/<int:n>')
class KospiTopNCorr(Resource):
    @ns.doc('list_kospi_topn_query')
    def get(self, abs, start_date, end_date, n):
        try:
            # 문자열을 boolean 값으로 변환
            abs_bool = abs.lower() in ['true', '1', 'yes'] # 리스트 안에 있는 문자면 True 반환
            result = topNcorr(current_app, abs_bool, start_date, end_date, n) # topNcorr 함수 호출
            print(result)
            return jsonify(result)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            current_app.sess_presto.close()
