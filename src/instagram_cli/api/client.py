import os
import requests
from pathlib import Path
from dotenv import load_dotenv

CONFIG_DIR = Path.home() / ".config" / "instagram-cli"
ENV_FILE = CONFIG_DIR / ".env"

load_dotenv(ENV_FILE)

ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN")
USER_ID = os.getenv("INSTAGRAM_USER_ID")

BASE_URL = "https://graph.instagram.com/v21.0"
REFRESH_URL = "https://graph.instagram.com/refresh_access_token"


def _get(path, params=None):
    response = requests.get(
        f"{BASE_URL}{path}",
        params={"access_token": ACCESS_TOKEN, **(params or {})},
    )
    data = response.json()
    if "error" in data:
        raise RuntimeError(data["error"]["message"])
    return data


def _post(path, data=None):
    response = requests.post(
        f"{BASE_URL}{path}",
        data={"access_token": ACCESS_TOKEN, **(data or {})},
    )
    result = response.json()
    if "error" in result:
        raise RuntimeError(result["error"]["message"])
    return result
