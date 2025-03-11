"""
This script starts the Flask application server.
"""

from app import create_app

if __name__ == '__main__': # 스크립트가 직접 실행될 때만 코드 실행. 다른 모듈에서 임포트될 때는 실행되지 않음.
    app = create_app() # create_app 함수 호출해 Flask 애플리케이션 인스턴스 생성(설정, 라우팅, 확장 등 초기화)
    app.run(debug=app.config['DEBUG']) # 생성된 Flask 애플리케이션 인스턴스 실행. 설정 파일에 정의된 DEBUG 값에 따라 디버그 모드 활성/비활성화
