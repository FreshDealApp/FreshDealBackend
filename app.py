import os
import sqlalchemy
from flask import Flask, redirect
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from dotenv import load_dotenv
from src.models import db
from src.routes import init_app
from flasgger import Swagger

# .env dosyasındaki ortam değişkenlerini yükle
load_dotenv()

def create_app():
    app = Flask(__name__)

    # Varsayılan ortam değişkenleri (test için)
    required_env_vars = {
        "DB_SERVER": os.getenv("DB_SERVER", "mock_db_server"),  # Varsayılan değerler
        "DB_NAME": os.getenv("DB_NAME", "mock_db_name"),
        "DB_USERNAME": os.getenv("DB_USERNAME", "mock_db_username"),
        "DB_PASSWORD": os.getenv("DB_PASSWORD", "mock_db_password"),
        "DB_DRIVER": os.getenv("DB_DRIVER", "mock_db_driver"),
        "JWT_SECRET_KEY": os.getenv("JWT_SECRET_KEY", "mock_jwt_secret_key"),
    }

    # Eksik ortam değişkenleri kontrolü
    missing_vars = [var for var, value in required_env_vars.items() if not value]
    if missing_vars:
        print(f"Warning: Missing environment variables: {', '.join(missing_vars)} (using default values)")

    # Veritabanı URI'sinin yapılandırılması
    app.config['SQLALCHEMY_DATABASE_URI'] = (
        f"mssql+pyodbc://{required_env_vars['DB_USERNAME']}:" 
        f"{required_env_vars['DB_PASSWORD']}@"
        f"{required_env_vars['DB_SERVER']}/"
        f"{required_env_vars['DB_NAME']}?driver={required_env_vars['DB_DRIVER']}"
    )
    # SQLAlchemy ayarları
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'uploads')

    # JWT ve diğer güvenlik yapılandırmaları
    app.config['JWT_SECRET_KEY'] = required_env_vars['JWT_SECRET_KEY']
    JWTManager(app)

    # Veritabanı başlangıcı
    db.init_app(app)

    with app.app_context():
        db.create_all()

    # Veritabanı bağlantısı testi
    try:
        engine = sqlalchemy.create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
        connection = engine.connect()
        connection.close()
        print("Database connection successful.")
    except Exception as e:
        print(f"Error connecting to the database: {e}")

    # Uygulama başlangıcı
    init_app(app)

    # CORS ayarları
    CORS(app, resources={r"/*": {"origins": "*"}})

    # Swagger/OpenAPI yapılandırması
    swagger_config = {
        "openapi": "3.0.0",  # OpenAPI 3.0 kullanılıyor
        "info": {
            "title": "Freshdeal API",
            "description": "API for Freshdeal application",
            "version": "1.0.0",
            "contact": {
                "name": "Freshdeal",
                "url": "https://github.com/FreshDealApp",
                "email": "",
            }
        },
        "servers": [
            {"url": "https://freshdealapi-fkfaajfaffh4c0ex.uksouth-01.azurewebsites.net/", "description": "Production server"},
            {"url": "http://localhost:8000", "description": "Local development server"},
        ],
        "components": {
            "securitySchemes": {
                "BearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT"
                }
            }
        },
        "security": [
            {"BearerAuth": []}
        ],
        "specs": [
            {
                "endpoint": 'apispec_1',
                "route": '/apispec_1.json',
                "rule_filter": lambda rule: True,  # Tüm API rotaları dahil
                "model_filter": lambda tag: True,  # Tüm etiketler dahil
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/swagger/",
    }

    Swagger(app, config=swagger_config)

    # Anasayfadan Swagger'a yönlendirme
    @app.route('/')
    def redirect_to_swagger():
        return redirect('/swagger')

    return app

# Uygulamanın çalıştırılması
app = create_app()

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000, debug=False)
