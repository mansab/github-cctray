"""Config Module"""
import os

API_BASE_URL = "https://api.github.com"
MAX_WORKERS = 10
TIMEOUT = 10

BASIC_AUTH_USERNAME = os.environ.get("BASIC_AUTH_USERNAME")
BASIC_AUTH_PASSWORD = os.environ.get("BASIC_AUTH_PASSWORD")

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
APP_AUTH_ID = os.environ.get("APP_AUTH_ID")
B64_APP_AUTH_PRIVATE_KEY = os.environ.get("B64_APP_AUTH_PRIVATE_KEY")
APP_AUTH_INSTALLATION_ID = os.environ.get("APP_AUTH_INSTALLATION_ID")
APP_AUTH_BASE_URL = "https://api.github.com"
