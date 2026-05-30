from instagram_cli.api.client import _get, USER_ID

_METRICS_BASE = "impressions,reach,saved,shares,likes,comments,total_interactions"
_METRICS_BY_TYPE = {
    "IMAGE": _METRICS_BASE + ",profile_visits,follows",
    "VIDEO": _METRICS_BASE + ",plays,ig_reels_avg_watch_time,ig_reels_video_view_total_time",
    "REELS": _METRICS_BASE + ",plays,ig_reels_avg_watch_time,ig_reels_video_view_total_time",
    "CAROUSEL_ALBUM": (
        "impressions,reach,saved,shares,likes,comments,total_interactions,"
        "carousel_album_impressions,carousel_album_reach,"
        "carousel_album_engagement,carousel_album_saved"
    ),
}


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


def get_media_insights(media_id):
    media = _get(f"/{media_id}", {"fields": "media_type"})
    media_type = media.get("media_type", "IMAGE")
    metrics = _METRICS_BY_TYPE.get(media_type, _METRICS_BASE)
    data = _get(f"/{media_id}/insights", {"metric": metrics, "period": "lifetime"})
    return data.get("data", [])
