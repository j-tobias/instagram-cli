import time
from instagram_cli.api.client import _get, _post, USER_ID


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


def wait_for_container(creation_id, timeout=300, interval=5):
    deadline = time.time() + timeout
    while time.time() < deadline:
        data = _get(f"/{creation_id}", {"fields": "status_code"})
        status = data.get("status_code", "")
        if status == "FINISHED":
            time.sleep(2)
            return
        if status == "ERROR":
            raise RuntimeError("Media container processing failed (status: ERROR)")
        time.sleep(interval)
    raise RuntimeError(f"Timed out after {timeout}s waiting for media container — Instagram is still processing the video. Try again later or use a shorter/smaller video.")


def publish_container(creation_id):
    return _post(f"/{USER_ID}/media_publish", {"creation_id": creation_id})["id"]


def post_image(image_url, caption=None):
    creation_id = create_image_container(image_url, caption)
    return publish_container(creation_id)


def post_reel(video_url, caption=None):
    creation_id = create_reel_container(video_url, caption)
    wait_for_container(creation_id)
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
