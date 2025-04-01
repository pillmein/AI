from flask import Flask
from api_analysis import blueprint as analysis_bp
from api_sup_recommendation import blueprint as sup_recommend_bp
from api_time_recommendation import blueprint as time_recommend_bp
from api_favorites import blueprint as favorites_bp
from api_health_problem import blueprint as health_bp
from api_ocr_analyze import blueprint as ocr_bp

app = Flask(__name__)

# 각 API Blueprint 등록
app.register_blueprint(analysis_bp, url_prefix='/analysis')
app.register_blueprint(sup_recommend_bp, url_prefix='/supplement')
app.register_blueprint(time_recommend_bp, url_prefix='/timing')
app.register_blueprint(favorites_bp, url_prefix='/favorites')
app.register_blueprint(health_bp, url_prefix='/health')
app.register_blueprint(ocr_bp, url_prefix='/ocr')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)