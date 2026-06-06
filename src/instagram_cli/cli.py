import os
import sys
import argparse
from pathlib import Path
from instagram_cli.tunnel import public_tunnel
from instagram_cli.api import (
    test_connection,
    get_profile,
    get_media_list,
    get_media,
    get_media_insights,
    post_image,
    post_reel,
    post_carousel,
    refresh_token,
    get_token_status,
    ENV_FILE,
)

def _is_local(s: str) -> bool:
    return not s.startswith(("http://", "https://"))


def _ngrok_token() -> str:
    tok = os.getenv("NGROK_AUTHTOKEN", "")
    if not tok:
        print(
            "Error: NGROK_AUTHTOKEN is not set.\n"
            "Add it to ~/.config/instagram-cli/.env or export it in your shell.\n"
            "Get your token at: https://dashboard.ngrok.com/get-started/your-authtoken"
        )
        sys.exit(1)
    return tok


USAGE_LIMITS = """
Usage limits (Instagram Graph API):
  - Publishing:   50 posts per 24-hour rolling window per account.
                  Carousels count as a single post toward this limit.
                  Check your current usage with the content_publishing_limit
                  endpoint if you need to stay within quota.
  - API calls:    Rate-limited per app/user pair based on impressions.
                  Formula: 4800 × number of impressions per 24 hours.
                  Exceeding this returns a 400 error with code 32.
  - Carousels:    2–10 items per post (images, videos, or mixed).

Credentials are read from environment variables (or a .env file):
  INSTAGRAM_ACCESS_TOKEN   Long-lived access token for your Instagram account
  INSTAGRAM_USER_ID        Numeric Instagram user ID
"""


def _print_dict(data):
    for key, value in data.items():
        print(f"  {key}: {value}")


def _print_media_list(items):
    for item in items:
        _print_dict(item)
        print()


def _print_insights(items):
    for item in items:
        value = item.get("values", [{}])[0].get("value", "n/a")
        print(f"  {item.get('title', 'unknown')}: {value}")
        print(f"    {item.get('description', '')}")
        print()


def main():
    parser = argparse.ArgumentParser(
        prog="instagram-cli",
        description=(
            "A CLI for the Instagram Graph API.\n\n"
            "Read your profile and media, fetch post engagement insights, or publish\n"
            "images, reels, and carousels directly from the terminal. All commands\n"
            "require a valid access token set via the INSTAGRAM_ACCESS_TOKEN environment variable."
        ),
        epilog=USAGE_LIMITS,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # connection
    subparsers.add_parser(
        "connection",
        help="Test the API connection and print your account info",
        description=(
            "Verifies that your access token and user ID are valid by fetching\n"
            "basic profile fields (id, username, follower count, media count).\n"
            "Useful for confirming credentials are set up correctly."
        ),
        epilog=(
            "Example:\n"
            "  instagram-cli connection"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # auth
    auth_parser = subparsers.add_parser(
        "auth",
        help="Manage your access token",
        description=(
            "Commands for managing your Instagram access token.\n\n"
            f"Credentials are stored in: {ENV_FILE}"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    auth_sub = auth_parser.add_subparsers(dest="auth_command", required=True)

    auth_sub.add_parser(
        "status",
        help="Show token status and expiry date",
        description=(
            "Displays whether a token and user ID are configured, and when the\n"
            "current token expires. The expiry date is stored locally after running\n"
            "'auth refresh' and is not fetched from Instagram."
        ),
        epilog=(
            "Example:\n"
            "  instagram-cli auth status"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    auth_sub.add_parser(
        "refresh",
        help="Refresh the access token (extends expiry by 60 days)",
        description=(
            "Extends your long-lived access token by another 60 days.\n"
            "The new token and its expiry date are written back to:\n\n"
            f"  {ENV_FILE}\n\n"
            "Tokens can only be refreshed when they are at least 24 hours old\n"
            "and have not yet expired. Run this periodically to avoid disruption."
        ),
        epilog=(
            "Example:\n"
            "  instagram-cli auth refresh"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # profile
    subparsers.add_parser(
        "profile",
        help="Print your Instagram profile fields",
        description=(
            "Fetches and prints your Instagram profile fields:\n\n"
            "  id               Numeric Instagram user ID\n"
            "  username         Instagram handle (without @)\n"
            "  name             Display name\n"
            "  followers_count  Total number of followers\n"
            "  media_count      Total number of published posts"
        ),
        epilog=(
            "Example:\n"
            "  instagram-cli profile"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # media
    media_parser = subparsers.add_parser(
        "media",
        help="Read your published media",
        description="Commands for reading published posts and fetching engagement insights.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    media_sub = media_parser.add_subparsers(dest="media_command", required=True)

    media_list_p = media_sub.add_parser(
        "list",
        help="List your most recent posts",
        description=(
            "Returns your most recently published posts in reverse chronological\n"
            "order. Each result includes:\n\n"
            "  id          Numeric media ID (use with 'media get' and 'media insights')\n"
            "  caption     Post caption text\n"
            "  media_type  IMAGE, VIDEO, REELS, or CAROUSEL_ALBUM\n"
            "  timestamp   ISO 8601 publish time (UTC)\n"
            "  permalink   Public URL to the post on Instagram"
        ),
        epilog=(
            "Examples:\n"
            "  instagram-cli media list\n"
            "  instagram-cli media list --limit 25"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    media_list_p.add_argument(
        "--limit",
        type=int,
        default=10,
        metavar="N",
        help="Maximum number of posts to return (default: 10)",
    )

    media_get_p = media_sub.add_parser(
        "get",
        help="Get details for a single post",
        description=(
            "Fetches full details for one media item by its ID:\n\n"
            "  id              Numeric media ID\n"
            "  caption         Post caption text\n"
            "  media_type      IMAGE, VIDEO, REELS, or CAROUSEL_ALBUM\n"
            "  timestamp       ISO 8601 publish time (UTC)\n"
            "  permalink       Public URL to the post on Instagram\n"
            "  like_count      Total number of likes\n"
            "  comments_count  Total number of comments\n\n"
            "Find the media ID by running 'instagram-cli media list'."
        ),
        epilog=(
            "Example:\n"
            "  instagram-cli media get 17854360229135492"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    media_get_p.add_argument(
        "media_id",
        help="Numeric ID of the media item (visible in 'media list' output)",
    )

    media_insights_p = media_sub.add_parser(
        "insights",
        help="Get engagement metrics for a post",
        description=(
            "Fetches lifetime engagement metrics for a post. Requires a Business\n"
            "or Creator account. Available metrics depend on media type:\n\n"
            "  All types:     reach, saved, shares, likes, comments,\n"
            "                 total_interactions\n"
            "  IMAGE only:    profile_visits, follows\n"
            "  VIDEO / REELS: views, ig_reels_avg_watch_time,\n"
            "                 ig_reels_video_view_total_time\n\n"
            "Find the media ID by running 'instagram-cli media list'."
        ),
        epilog=(
            "Example:\n"
            "  instagram-cli media insights 17854360229135492"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    media_insights_p.add_argument(
        "media_id",
        help="Numeric ID of the media item (visible in 'media list' output)",
    )

    # post
    post_parser = subparsers.add_parser(
        "post",
        help="Publish a new post",
        description=(
            "Publish a new image, reel, or carousel to your Instagram account.\n\n"
            "Note: Instagram enforces a limit of 50 published posts per 24-hour\n"
            "rolling window. Carousels count as a single post."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    post_sub = post_parser.add_subparsers(dest="post_command", required=True)

    post_image_p = post_sub.add_parser(
        "image",
        help="Publish a single image post",
        description=(
            "Publishes a single image to your feed.\n\n"
            "Pass a local file path or a publicly accessible HTTPS URL.\n"
            "Local files are served temporarily via an ngrok tunnel\n"
            "(requires NGROK_AUTHTOKEN in ~/.config/instagram-cli/.env).\n\n"
            "Supported formats: JPEG. Max file size: 8 MB.\n"
            "Aspect ratios: 4:5 (portrait) to 1.91:1 (landscape)."
        ),
        epilog=(
            "Examples:\n"
            "  instagram-cli post image ./photo.jpg\n"
            "  instagram-cli post image ./photo.jpg --caption \"Hello world #instagram\"\n"
            "  instagram-cli post image https://example.com/photo.jpg"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    post_image_p.add_argument(
        "url",
        help="HTTPS URL or local file path of the image to post",
    )
    post_image_p.add_argument(
        "--caption",
        metavar="TEXT",
        help="Caption for the post (optional). Supports hashtags and @mentions.",
    )

    post_reel_p = post_sub.add_parser(
        "reel",
        help="Publish a reel (short video)",
        description=(
            "Publishes a video as an Instagram Reel.\n\n"
            "Pass a local file path or a publicly accessible HTTPS URL.\n"
            "Local files are served temporarily via an ngrok tunnel\n"
            "(requires NGROK_AUTHTOKEN in ~/.config/instagram-cli/.env).\n"
            "The tunnel stays open while Instagram processes the video.\n\n"
            "Requirements: MOV or MP4 (H.264 codec), AAC audio, 30 fps max,\n"
            "minimum 720px width, aspect ratio 9:16, duration 3–90 seconds."
        ),
        epilog=(
            "Examples:\n"
            "  instagram-cli post reel ./clip.mp4\n"
            "  instagram-cli post reel ./clip.mp4 --caption \"My reel #video\"\n"
            "  instagram-cli post reel https://example.com/video.mp4"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    post_reel_p.add_argument(
        "url",
        help="HTTPS URL or local file path of the video to post",
    )
    post_reel_p.add_argument(
        "--caption",
        metavar="TEXT",
        help="Caption for the reel (optional). Supports hashtags and @mentions.",
    )

    post_carousel_p = post_sub.add_parser(
        "carousel",
        help="Publish a carousel of images and/or videos (2–10 items)",
        description=(
            "Publishes 2 to 10 images and/or videos as a single swipeable carousel post.\n"
            "Positional args are image paths/URLs; use --video for video items.\n\n"
            "Local file paths are served temporarily via an ngrok tunnel\n"
            "(requires NGROK_AUTHTOKEN in ~/.config/instagram-cli/.env).\n"
            "You can freely mix local paths and remote URLs in the same carousel.\n\n"
            "Note: all image items are added first (in order), followed by all --video\n"
            "items (in order). Mixed ordering is not supported.\n\n"
            "Image requirements: JPEG, max 8 MB, aspect ratio 4:5 to 1.91:1.\n"
            "Video requirements: MOV or MP4 (H.264), AAC audio, max 60 seconds.\n\n"
            "Examples:\n"
            "  instagram-cli post carousel ./1.jpg ./2.jpg\n"
            "  instagram-cli post carousel ./photo.jpg \\\n"
            "                              --video ./clip.mp4 \\\n"
            "                              --caption \"My carousel\"\n"
            "  instagram-cli post carousel https://example.com/1.jpg \\\n"
            "                              https://example.com/2.jpg"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    post_carousel_p.add_argument(
        "urls",
        nargs="*",
        metavar="URL",
        help="HTTPS URL or local file path for image items (optional if --video is used)",
    )
    post_carousel_p.add_argument(
        "--video",
        dest="video_urls",
        action="append",
        default=[],
        metavar="URL",
        help="HTTPS URL or local file path for a video item; repeat for multiple videos",
    )
    post_carousel_p.add_argument(
        "--caption",
        metavar="TEXT",
        help="Caption for the carousel post (optional). Supports hashtags and @mentions.",
    )

    args = parser.parse_args()

    try:
        if args.command == "connection":
            test_connection()

        elif args.command == "auth":
            if args.auth_command == "status":
                _print_dict(get_token_status())
            elif args.auth_command == "refresh":
                result = refresh_token()
                print(f"Token refreshed. Expires: {result['expires_at']}")

        elif args.command == "profile":
            _print_dict(get_profile())

        elif args.command == "media":
            if args.media_command == "list":
                _print_media_list(get_media_list(limit=args.limit))
            elif args.media_command == "get":
                _print_dict(get_media(args.media_id))
            elif args.media_command == "insights":
                _print_insights(get_media_insights(args.media_id))

        elif args.command == "post":
            if args.post_command == "image":
                if _is_local(args.url):
                    p = Path(args.url)
                    if not p.exists():
                        print(f"Error: file not found: {p}")
                        sys.exit(1)
                    print(f"  Starting public tunnel for {p.name}...", file=sys.stderr)
                    with public_tunnel([p], authtoken=_ngrok_token()) as url_for:
                        post_id = post_image(url_for(p), caption=args.caption)
                else:
                    post_id = post_image(args.url, caption=args.caption)
                print(f"Posted: {post_id}")
            elif args.post_command == "reel":
                if _is_local(args.url):
                    p = Path(args.url)
                    if not p.exists():
                        print(f"Error: file not found: {p}")
                        sys.exit(1)
                    print(f"  Starting public tunnel for {p.name}...", file=sys.stderr)
                    with public_tunnel([p], authtoken=_ngrok_token()) as url_for:
                        post_id = post_reel(url_for(p), caption=args.caption)
                else:
                    post_id = post_reel(args.url, caption=args.caption)
                print(f"Posted: {post_id}")
            elif args.post_command == "carousel":
                all_image_urls = list(args.urls)
                all_video_urls = list(args.video_urls)
                items = [{"image_url": u} for u in all_image_urls]
                items += [{"video_url": u} for u in all_video_urls]
                if not 2 <= len(items) <= 10:
                    print("Error: carousel requires between 2 and 10 items (images + videos)")
                    sys.exit(1)
                local_paths = [
                    Path(u) for u in all_image_urls + all_video_urls if _is_local(u)
                ]
                for p in local_paths:
                    if not p.exists():
                        print(f"Error: file not found: {p}")
                        sys.exit(1)
                if local_paths:
                    print(f"  Starting public tunnel for {len(local_paths)} file(s)...", file=sys.stderr)
                    with public_tunnel(local_paths, authtoken=_ngrok_token()) as url_for:
                        resolved = [
                            {"image_url": url_for(Path(u)) if _is_local(u) else u}
                            for u in all_image_urls
                        ] + [
                            {"video_url": url_for(Path(u)) if _is_local(u) else u}
                            for u in all_video_urls
                        ]
                        post_id = post_carousel(resolved, caption=args.caption)
                else:
                    post_id = post_carousel(items, caption=args.caption)
                print(f"Posted: {post_id}")

    except RuntimeError as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
