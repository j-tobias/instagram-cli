import os
import requests
from datetime import datetime, timedelta, timezone
from dotenv import set_key
from instagram_cli.api.client import (
    ACCESS_TOKEN,
    USER_ID,
    REFRESH_URL,
    CONFIG_DIR,
    ENV_FILE,
    _get,
)


def refresh_token():
    response = requests.get(
        REFRESH_URL,
        params={"grant_type": "ig_refresh_token", "access_token": ACCESS_TOKEN},
    )
    data = response.json()
    if "error" in data:
        raise RuntimeError(data["error"]["message"])

    new_token = data["access_token"]
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=data["expires_in"])
    expires_str = expires_at.strftime("%Y-%m-%d")

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    ENV_FILE.touch(exist_ok=True)
    set_key(ENV_FILE, "INSTAGRAM_ACCESS_TOKEN", new_token)
    set_key(ENV_FILE, "INSTAGRAM_TOKEN_EXPIRES_AT", expires_str)

    return {"access_token": new_token, "expires_at": expires_str}


def get_token_status():
    expires_at = os.getenv("INSTAGRAM_TOKEN_EXPIRES_AT")
    return {
        "token_set": ACCESS_TOKEN is not None,
        "user_id_set": USER_ID is not None,
        "expires_at": expires_at or "unknown (run 'auth refresh' to store expiry)",
    }


def test_connection():
    try:
        profile = _get(f"/{USER_ID}", {"fields": "id,username,name,followers_count,media_count"})
        print("Connection successful!")
        for key, value in profile.items():
            print(f"  {key}: {value}")
    except RuntimeError as e:
        print(f"Error: {e}")
