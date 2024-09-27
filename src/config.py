"""Config Module"""
import os

API_BASE_URL = "https://api.github.com"
MAX_WORKERS = 10
TIMEOUT = 10

LOGIN_USER = os.environ.get("LOGIN_USER")
LOGIN_PASSWORD = os.environ.get("LOGIN_PASSWORD")

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_APP_TOKEN = os.environ.get("GITHUB_APP_TOKEN")
APP_AUTH_ID = "Iv1.029716a4d1524dcd"
