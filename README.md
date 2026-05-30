<p align="center">
  <img src="resources/InstagramCLI.png" alt="Instagram CLI" width="100%">
</p>

<div align="center">

[Quick Start](#quick-start) · [Commands](#commands) · [Auth](#auth) · [Usage Limits](#usage-limits)

</div>

---

## What is instagram-cli?

A terminal interface for the Instagram Graph API.

Read your profile and media, and publish images, reels, and carousels directly from the command line — no browser, no dashboard. Built as a `uv`-installable Python package with a clean two-layer design: an API module you can import, and a CLI on top of it.

---

## Quick Start

**Install:**

```bash
uv pip install -e .
```

**Configure credentials** in `~/.config/instagram-cli/.env`:

```ini
INSTAGRAM_ACCESS_TOKEN=your_long_lived_token
INSTAGRAM_USER_ID=your_numeric_user_id
```

**Verify the connection:**

```bash
instagram-cli connection
```

---

## Commands

### Profile

```bash
instagram-cli profile
```

Prints your account fields: id, username, name, followers\_count, media\_count.

---

### Media

```bash
instagram-cli media list           # 10 most recent posts
instagram-cli media list --limit 25
instagram-cli media get <media_id>
```

`list` returns id, caption, media\_type, timestamp, and permalink per item.
`get` additionally returns like\_count and comments\_count.

---

### Post

Publish a single image:

```bash
instagram-cli post image https://example.com/photo.jpg --caption "Hello"
```

Publish a reel:

```bash
instagram-cli post reel https://example.com/clip.mp4 --caption "My reel"
```

Publish a carousel (2–10 images):

```bash
instagram-cli post carousel https://example.com/1.jpg \
                            https://example.com/2.jpg \
                            https://example.com/3.jpg \
                            --caption "Swipe →"
```

Media must be hosted at a publicly accessible HTTPS URL. Instagram fetches it at publish time.

| Type | Format | Max size | Aspect ratio |
|---|---|---|---|
| Image | JPEG | 8 MB | 4:5 to 1.91:1 |
| Reel | MP4 / MOV (H.264, AAC) | — | 9:16, 3–90 sec |
| Carousel | JPEG per item | 8 MB each | 4:5 to 1.91:1 |

---

### Auth

```bash
instagram-cli auth status    # show token config and expiry date
instagram-cli auth refresh   # extend token by 60 days
```

`refresh` calls the Instagram token refresh endpoint and writes the new token and expiry date back to `~/.config/instagram-cli/.env`. Run it periodically — tokens expire after 60 days.

---

## Usage Limits

| Limit | Value |
|---|---|
| Posts per 24-hour window | 50 (carousels count as 1) |
| Carousel items per post | 2–10 |
| API call rate | 4800 × impressions per 24 hours |
| Token lifetime | 60 days (refresh with `auth refresh`) |

---

## Credentials

All credentials are read from `~/.config/instagram-cli/.env`:

```ini
INSTAGRAM_ACCESS_TOKEN=your_long_lived_token
INSTAGRAM_USER_ID=your_numeric_user_id
INSTAGRAM_TOKEN_EXPIRES_AT=2026-07-29   # written automatically by auth refresh
```

Long-lived tokens must be obtained once through the [Meta developer console](https://developers.facebook.com/docs/instagram-platform/). After that, `auth refresh` keeps them alive.
