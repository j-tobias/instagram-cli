import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def _probe(path: Path) -> dict:
    if not shutil.which("ffprobe"):
        return {}
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams", str(path)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return {}
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {}


def check_reel(path: Path) -> list[str]:
    """Return quality warnings for a reel file. Empty list means all good (or ffprobe unavailable)."""
    data = _probe(path)
    if not data:
        return []

    warnings = []
    streams = data.get("streams", [])
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    audio = next((s for s in streams if s.get("codec_type") == "audio"), None)

    if video:
        codec = video.get("codec_name", "").lower()
        if codec != "h264":
            warnings.append(f"video codec is '{codec}', expected h264")

        width = int(video.get("width", 0))
        height = int(video.get("height", 0))
        if width < 720:
            warnings.append(f"width {width}px is below the 720px minimum")
        elif width < 1080:
            warnings.append(f"width {width}px — recommend 1080px for best quality")

        fps_str = video.get("r_frame_rate", "0/1")
        try:
            num, den = map(int, fps_str.split("/"))
            fps = num / den if den else 0
            if fps > 30:
                warnings.append(f"frame rate {fps:.1f}fps exceeds the 30fps limit")
        except (ValueError, ZeroDivisionError):
            pass

        if width and height:
            ratio = width / height
            if abs(ratio - 9 / 16) > 0.05:
                warnings.append(f"aspect ratio {width}:{height} is not 9:16")

        duration = float(video.get("duration", 0))
        if duration > 0 and duration < 3:
            warnings.append(f"duration {duration:.1f}s is below the 3s minimum")
        elif duration > 90:
            warnings.append(f"duration {duration:.1f}s exceeds the 90s limit")

    if audio is None:
        warnings.append("no audio stream found (AAC audio is required)")
    else:
        audio_codec = audio.get("codec_name", "").lower()
        if audio_codec != "aac":
            warnings.append(f"audio codec is '{audio_codec}', expected aac")

    return warnings


def transcode_reel(src: Path) -> Path:
    """Transcode src to optimal Instagram Reel spec. Returns a temp Path; caller must unlink it."""
    if not shutil.which("ffmpeg"):
        raise RuntimeError(
            "ffmpeg is not installed or not on PATH.\n"
            "Install it first:  brew install ffmpeg  or  apt install ffmpeg"
        )

    tmp = tempfile.NamedTemporaryFile(suffix=".mp4", prefix="instagram_reel_", delete=False)
    tmp.close()
    out = Path(tmp.name)

    cmd = [
        "ffmpeg", "-y", "-i", str(src),
        "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2",
        "-c:v", "libx264",
        "-profile:v", "high",
        "-pix_fmt", "yuv420p",
        "-r", "30",
        "-c:a", "aac",
        "-b:a", "192k",
        "-movflags", "+faststart",
        str(out),
    ]

    print("  Transcoding to optimal reel spec (1080×1920, H.264, AAC 192k, 30fps)...", file=sys.stderr)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        out.unlink(missing_ok=True)
        raise RuntimeError(f"ffmpeg transcoding failed:\n{result.stderr[-2000:]}")

    return out
