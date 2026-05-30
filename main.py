import os
import requests
from dotenv import load_dotenv

load_dotenv()

ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN")
USER_ID = os.getenv("INSTAGRAM_USER_ID")

BASE_URL = "https://graph.instagram.com/v21.0"


def test_connection():
    response = requests.get(
        f"{BASE_URL}/{USER_ID}",
        params={
            "fields": "id,username,name,followers_count,media_count",
            "access_token": ACCESS_TOKEN,
        },
    )
    data = response.json()

    if "error" in data:
        print(f"Error: {data['error']['message']}")
    else:
        print("Connection successful!")
        for key, value in data.items():
            print(f"  {key}: {value}")


if __name__ == "__main__":
    test_connection()
