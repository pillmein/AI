from flask import Flask
from flasgger import Swagger
from flask_jwt_extended import JWTManager
from config import SECRET_KEY

# 모든 blueprint import
from api_analysis import blueprint as analysis_bp
from api_favorites import blueprint as favorites_bp
from api_health_problem import blueprint as health_bp
from api_ocr_analyze import blueprint as ocr_bp
from api_sup_recommendation import blueprint as recommend_bp
from api_time_recommendation import blueprint as time_bp

app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = SECRET_KEY

app.config['SWAGGER'] = {
    'title': 'My API',
    'uiversion': 3,
    'securityDefinitions': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header',
            'description': "Enter JWT token as: **Bearer YOUR_TOKEN_HERE**"
        }
    },
    'security': [
        {'Bearer': []}
    ]
}

Swagger(app)
JWTManager(app)

# blueprint 등록
app.register_blueprint(analysis_bp, url_prefix='/analysis')
app.register_blueprint(favorites_bp, url_prefix='/favorites')
app.register_blueprint(health_bp, url_prefix='/health')
app.register_blueprint(ocr_bp, url_prefix='/ocr')
app.register_blueprint(recommend_bp, url_prefix='/supplement')
app.register_blueprint(time_bp, url_prefix='/timing')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)