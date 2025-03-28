from flask import Flask
from health_problem import health_blueprint

app = Flask(__name__)

# 블루프린트 등록 (모듈화된 API 추가)
app.register_blueprint(health_blueprint, url_prefix="/health")

@app.route("/")
def home():
    return {"message": "Pill Me In"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
