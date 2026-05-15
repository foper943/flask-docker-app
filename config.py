import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    PORT = int(os.getenv("PORT", 5000))
    DEBUG = os.getenv("DEBUG", "True") == "True"
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///default.db")
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-in-production")