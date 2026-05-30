import os
import requests
from dotenv import load_dotenv

load_dotenv()

ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN")
USER_ID = os.getenv("INSTAGRAM_USER_ID")

BASE_URL = "https://graph.instagram.com/v21.0"


def _get(path, params=None):
    response = requests.get(
        f"{BASE_URL}{path}",
        params={"access_token": ACCESS_TOKEN, **(params or {})},
    )
    data = response.json()
    if "error" in data:
        raise RuntimeError(data["error"]["message"])
    return data


def get_profile():
    return _get(
        f"/{USER_ID}",
        {"fields": "id,username,name,followers_count,media_count"},
    )


def get_media_list(limit=10):
    data = _get(
        f"/{USER_ID}/media",
        {
            "fields": "id,caption,media_type,timestamp,permalink",
            "limit": limit,
        },
    )
    return data.get("data", [])


def get_media(media_id):
    return _get(
        f"/{media_id}",
        {"fields": "id,caption,media_type,timestamp,permalink,like_count,comments_count"},
    )


def _post(path, data=None):
    response = requests.post(
        f"{BASE_URL}{path}",
        data={"access_token": ACCESS_TOKEN, **(data or {})},
    )
    result = response.json()
    if "error" in result:
        raise RuntimeError(result["error"]["message"])
    return result


def create_image_container(image_url, caption=None):
    payload = {"image_url": image_url}
    if caption:
        payload["caption"] = caption
    return _post(f"/{USER_ID}/media", payload)["id"]


def create_reel_container(video_url, caption=None):
    payload = {"video_url": video_url, "media_type": "REELS"}
    if caption:
        payload["caption"] = caption
    return _post(f"/{USER_ID}/media", payload)["id"]


def create_carousel_item(image_url=None, video_url=None):
    payload = {"is_carousel_item": "true"}
    if image_url:
        payload["image_url"] = image_url
    elif video_url:
        payload["video_url"] = video_url
    else:
        raise ValueError("Either image_url or video_url is required")
    return _post(f"/{USER_ID}/media", payload)["id"]


def create_carousel_container(children, caption=None):
    payload = {"media_type": "CAROUSEL", "children": ",".join(children)}
    if caption:
        payload["caption"] = caption
    return _post(f"/{USER_ID}/media", payload)["id"]


def publish_container(creation_id):
    return _post(f"/{USER_ID}/media_publish", {"creation_id": creation_id})["id"]


def post_image(image_url, caption=None):
    creation_id = create_image_container(image_url, caption)
    return publish_container(creation_id)


def post_reel(video_url, caption=None):
    creation_id = create_reel_container(video_url, caption)
    return publish_container(creation_id)


def post_carousel(items, caption=None):
    children = [
        create_carousel_item(
            image_url=item.get("image_url"),
            video_url=item.get("video_url"),
        )
        for item in items
    ]
    creation_id = create_carousel_container(children, caption)
    return publish_container(creation_id)


def test_connection():
    try:
        profile = get_profile()
        print("Connection successful!")
        for key, value in profile.items():
            print(f"  {key}: {value}")
    except RuntimeError as e:
        print(f"Error: {e}")
