import sys
import argparse
from instagram_cli.api import (
    test_connection,
    get_profile,
    get_media_list,
    get_media,
    post_image,
    post_reel,
    post_carousel,
)

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


def main():
    parser = argparse.ArgumentParser(
        prog="instagram-cli",
        description=(
            "A CLI for the Instagram Graph API.\n\n"
            "Read your profile and media, or publish images, reels, and carousels\n"
            "directly from the terminal. All commands require a valid access token\n"
            "set via the INSTAGRAM_ACCESS_TOKEN environment variable."
        ),
        epilog=USAGE_LIMITS,
        formatter_class=argparse.RawDescriptionHelpFormatter,
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
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # profile
    subparsers.add_parser(
        "profile",
        help="Print your Instagram profile fields",
        description=(
            "Fetches and prints your Instagram profile: id, username, name,\n"
            "followers_count, and media_count."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # media
    media_parser = subparsers.add_parser(
        "media",
        help="Read your published media",
        description="Commands for reading published posts on your account.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    media_sub = media_parser.add_subparsers(dest="media_command", required=True)

    media_list_p = media_sub.add_parser(
        "list",
        help="List your most recent posts",
        description=(
            "Returns your most recently published posts in reverse chronological\n"
            "order. Each result includes id, caption, media_type, timestamp,\n"
            "and permalink."
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
            "Fetches full details for one media item by its ID, including\n"
            "id, caption, media_type, timestamp, permalink, like_count,\n"
            "and comments_count."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    media_get_p.add_argument(
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
            "Publishes a single image to your feed. The image must be hosted at\n"
            "a publicly accessible HTTPS URL. Instagram will fetch it at publish\n"
            "time, so it must remain accessible until the post goes live.\n\n"
            "Supported formats: JPEG. Max file size: 8 MB.\n"
            "Aspect ratios: 4:5 (portrait) to 1.91:1 (landscape)."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    post_image_p.add_argument(
        "url",
        help="Publicly accessible HTTPS URL of the image to post",
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
            "Publishes a video as an Instagram Reel. The video must be hosted at\n"
            "a publicly accessible HTTPS URL.\n\n"
            "Requirements: MOV or MP4 (H.264 codec), AAC audio, 30 fps max,\n"
            "minimum 720px width, aspect ratio 9:16, duration 3–90 seconds."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    post_reel_p.add_argument(
        "url",
        help="Publicly accessible HTTPS URL of the video to post",
    )
    post_reel_p.add_argument(
        "--caption",
        metavar="TEXT",
        help="Caption for the reel (optional). Supports hashtags and @mentions.",
    )

    post_carousel_p = post_sub.add_parser(
        "carousel",
        help="Publish a carousel of images (2–10 items)",
        description=(
            "Publishes multiple images as a single swipeable carousel post.\n"
            "Pass 2 to 10 publicly accessible image URLs as positional arguments.\n\n"
            "Each image must meet the same requirements as a single image post\n"
            "(JPEG, max 8 MB, aspect ratio 4:5 to 1.91:1). All images in a\n"
            "carousel are cropped to a square (1:1) in the feed thumbnail.\n\n"
            "Example:\n"
            "  instagram-cli post carousel https://example.com/1.jpg \\\n"
            "                              https://example.com/2.jpg \\\n"
            "                              --caption \"My carousel\""
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    post_carousel_p.add_argument(
        "urls",
        nargs="+",
        metavar="URL",
        help="Publicly accessible HTTPS image URLs (2–10 required)",
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

        elif args.command == "profile":
            _print_dict(get_profile())

        elif args.command == "media":
            if args.media_command == "list":
                _print_media_list(get_media_list(limit=args.limit))
            elif args.media_command == "get":
                _print_dict(get_media(args.media_id))

        elif args.command == "post":
            if args.post_command == "image":
                post_id = post_image(args.url, caption=args.caption)
                print(f"Posted: {post_id}")
            elif args.post_command == "reel":
                post_id = post_reel(args.url, caption=args.caption)
                print(f"Posted: {post_id}")
            elif args.post_command == "carousel":
                if not 2 <= len(args.urls) <= 10:
                    print("Error: carousel requires between 2 and 10 image URLs")
                    sys.exit(1)
                items = [{"image_url": url} for url in args.urls]
                post_id = post_carousel(items, caption=args.caption)
                print(f"Posted: {post_id}")

    except RuntimeError as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
