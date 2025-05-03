import os
import sqlalchemy
from flask import Flask, redirect
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from dotenv import load_dotenv
from src.models import db
from src.routes import init_app
from flasgger import Swagger

load_dotenv()

def create_app():
    app = Flask(__name__)

    required_env_vars = {
        "DB_SERVER": os.getenv("DB_SERVER"),  # test
        "DB_NAME": os.getenv("DB_NAME"),
        "DB_USERNAME": os.getenv("DB_USERNAME"),
        "DB_PASSWORD": os.getenv("DB_PASSWORD"),
        "DB_DRIVER": os.getenv("DB_DRIVER"),
        "JWT_SECRET_KEY": os.getenv("JWT_SECRET_KEY"),
    }

    missing_vars = [var for var, value in required_env_vars.items() if not value]
    if missing_vars:
        raise SystemExit(f"Error: Missing environment variables: {', '.join(missing_vars)}")

    app.config['SQLALCHEMY_DATABASE_URI'] = (
        f"mssql+pyodbc://{required_env_vars['DB_USERNAME']}:" 
        f"{required_env_vars['DB_PASSWORD']}@"
        f"{required_env_vars['DB_SERVER']}/"
        f"{required_env_vars['DB_NAME']}?driver={required_env_vars['DB_DRIVER']}"
    )

    # app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:123456789@127.0.0.1:3306/freshdeallocal'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'uploads')

    app.config['JWT_SECRET_KEY'] = required_env_vars['JWT_SECRET_KEY']
    JWTManager(app)

    db.init_app(app)

    with app.app_context():
        db.create_all()
        try:
            from src.services.achievement_service import AchievementService
            AchievementService.initialize_achievements()
            print("Achievements initialized successfully")
        except Exception as e:
            print(f"Error initializing achievements: {e}")

    try:
        engine = sqlalchemy.create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
        connection = engine.connect()
        connection.close()
        print("Database connection successful.")
    except Exception as e:
        print(f"Error connecting to the database: {e}")

    init_app(app)

    CORS(app, resources={r"/*": {"origins": "*"}})

    # Flasgger setup with OpenAPI 3.0 and global security definitions
    swagger_config = {
        "openapi": "3.0.0",  # Using OpenAPI 3.0
        "info": {
            "title": "Freshdeal API",
            "description": "API for Freshdeal application"
                           ,
            "version": "1.0.0",
            "contact": {
                "name": "Freshdeal",
                "url": "https://github.com/FreshDealApp",
                "email": "",

            }
        },
        "servers": [
            {"url": "https://freshdealbackend.azurewebsites.net/",
             "description": "Production server"},
            {"url": "http://localhost:8000", "description": "Local development server"},


        ],
        # Global security scheme using JWT bearer token
        "components": {
            "securitySchemes": {
                "BearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT"
                }
            }
        },
        # Apply the security scheme globally to all endpoints
        "security": [
            {
                "BearerAuth": []
            }
        ],
        "specs": [
            {
                "endpoint": 'apispec_1',
                "route": '/apispec_1.json',
                "rule_filter": lambda rule: True,  # Include all API routes
                "model_filter": lambda tag: True,  # Include all tags
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/swagger/",
        "headers": [],
    }

    Swagger(app, config=swagger_config)

    @app.route('/')
    def redirect_to_swagger():
        return redirect('/swagger')

    return app

app = create_app()

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=False)
