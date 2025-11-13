from flask import Flask, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import os
from db import db, init_db
from routes import bp
from flask_swagger_ui import get_swaggerui_blueprint

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

load_dotenv()
app = Flask(__name__)

SWAGGER_URL = "/apidocs"       
API_URL = "/swagger.yaml"   

swaggerui_bp = get_swaggerui_blueprint(
    SWAGGER_URL,              
    API_URL,                 
    config={"app_name": "Inforens Chatbot APIs"}
)
app.register_blueprint(swaggerui_bp, url_prefix=SWAGGER_URL)

@app.route("/swagger.yaml")
def swagger_spec():
    return send_from_directory(
        os.path.join(app.root_path, "specs"), "api_spec.yaml"
    )


app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['PERPLEXITY_API_KEY'] = os.getenv('PERPLEXITY_API_KEY')
app.config['CONTENT_FILE'] = os.getenv('CONTENT_FILE')
app.config['SESSION_COOKIE_SECURE'] = True
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


init_db(app)
app.register_blueprint(bp)
CORS(app, origins=["https://inforens-chatbot.vercel.app"], supports_credentials=True)

if __name__ == "__main__":
    app.run(debug=True)
