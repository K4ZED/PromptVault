import os

from dotenv import load_dotenv


load_dotenv()

database_url = os.getenv("DATABASE_URL")
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = database_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 280,
    }
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("FLASK_ENV") == "production"
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_SECURE = os.getenv("FLASK_ENV") == "production"
    MAX_CONTENT_LENGTH = 1 * 1024 * 1024
    AUTO_CREATE_TABLES = os.getenv("AUTO_CREATE_TABLES", "true").lower() == "true"
    RESET_CONTENT_TASKS_DAILY = os.getenv("RESET_CONTENT_TASKS_DAILY", "true").lower() == "true"
    APP_TIMEZONE = os.getenv("APP_TIMEZONE", "Asia/Jakarta")
