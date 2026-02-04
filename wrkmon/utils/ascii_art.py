"""ASCII art generator for YouTube thumbnails - Enhanced with colors and blocks."""

import asyncio
import io
import logging
import urllib.request
from pathlib import Path
from typing import Optional

logger = logging.getLogger("wrkmon.ascii_art")

# Character sets for different styles
CHARS_BLOCKS = "█▓▒░ "  # Block characters (best for images)
CHARS_BLOCKS_DETAILED = "████▓▓▒▒░░  "  # More gradients
CHARS_ASCII = "@%#*+=-:. "  # Classic ASCII
CHARS_BRAILLE = "⣿⣷⣯⣟⡿⢿⣻⣽⣾⣶⣦⣤⣀⡀ "  # Braille patterns

# Color palette for Rich markup (approximate colors)
COLOR_PALETTE = [
    "#000000", "#1a1a1a", "#333333", "#4d4d4d", "#666666",
    "#808080", "#999999", "#b3b3b3", "#cccccc", "#e6e6e6", "#ffffff"
]

# Extended color palette for better color representation
EXTENDED_COLORS = {
    (0, 0, 0): "black",
    (255, 255, 255): "white",
    (255, 0, 0): "red",
    (0, 255, 0): "green",
    (0, 0, 255): "blue",
    (255, 255, 0): "yellow",
    (255, 0, 255): "magenta",
    (0, 255, 255): "cyan",
    (128, 128, 128): "grey50",
    (192, 192, 192): "grey74",
    (128, 0, 0): "dark_red",
    (0, 128, 0): "dark_green",
    (0, 0, 128): "dark_blue",
    (128, 128, 0): "olive",
    (128, 0, 128): "purple",
    (0, 128, 128): "teal",
}


def get_thumbnail_url(video_id: str, quality: str = "mqdefault") -> str:
    """
    Get YouTube thumbnail URL for a video.

    Quality options:
    - default: 120x90
    - mqdefault: 320x180
    - hqdefault: 480x360
    - sddefault: 640x480
    - maxresdefault: 1280x720
    """
    return f"https://img.youtube.com/vi/{video_id}/{quality}.jpg"


def download_thumbnail(video_id: str, quality: str = "mqdefault") -> Optional[bytes]:
    """Download thumbnail image from YouTube."""
    url = get_thumbnail_url(video_id, quality)
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            return response.read()
    except Exception as e:
        logger.debug(f"Failed to download thumbnail: {e}")
        return None


async def download_thumbnail_async(video_id: str, quality: str = "mqdefault") -> Optional[bytes]:
    """Async version of download_thumbnail."""
    return await asyncio.to_thread(download_thumbnail, video_id, quality)


def find_closest_color(r: int, g: int, b: int) -> str:
    """Find the closest named color for Rich markup."""
    min_dist = float('inf')
    closest = "white"

    for (cr, cg, cb), name in EXTENDED_COLORS.items():
        dist = (r - cr) ** 2 + (g - cg) ** 2 + (b - cb) ** 2
        if dist < min_dist:
            min_dist = dist
            closest = name

    return closest


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """Convert RGB to hex color."""
    return f"#{r:02x}{g:02x}{b:02x}"


def image_to_ascii_blocks(
    image_data: bytes,
    width: int = 40,
    colored: bool = True,
) -> str:
    """
    Convert image to colored block ASCII art.

    Uses half-block characters (▀▄) to achieve 2x vertical resolution
    with foreground and background colors.
    """
    try:
        from PIL import Image
    except ImportError:
        logger.warning("Pillow not installed")
        return ""

    try:
        img = Image.open(io.BytesIO(image_data))

        # Calculate dimensions (2 pixels per character vertically)
        aspect_ratio = img.height / img.width
        char_height = int(width * aspect_ratio * 0.5)  # Half because we use half-blocks
        pixel_height = char_height * 2

        # Resize
        img = img.resize((width, pixel_height))
        img = img.convert("RGB")
        pixels = list(img.getdata())

        lines = []
        for y in range(0, pixel_height, 2):
            line = ""
            for x in range(width):
                # Top pixel
                top_idx = y * width + x
                # Bottom pixel
                bot_idx = (y + 1) * width + x if (y + 1) < pixel_height else top_idx

                top_r, top_g, top_b = pixels[top_idx]
                bot_r, bot_g, bot_b = pixels[bot_idx]

                if colored:
                    # Use half-block with fg (top) and bg (bottom) colors
                    top_hex = rgb_to_hex(top_r, top_g, top_b)
                    bot_hex = rgb_to_hex(bot_r, bot_g, bot_b)
                    line += f"[{top_hex} on {bot_hex}]▀[/]"
                else:
                    # Grayscale block
                    avg = (top_r + top_g + top_b + bot_r + bot_g + bot_b) // 6
                    char_idx = int(avg / 256 * len(CHARS_BLOCKS))
                    char_idx = min(char_idx, len(CHARS_BLOCKS) - 1)
                    line += CHARS_BLOCKS[char_idx]

            lines.append(line)

        return "\n".join(lines)

    except Exception as e:
        logger.debug(f"Failed to convert image: {e}")
        return ""


def image_to_ascii_simple(
    image_data: bytes,
    width: int = 40,
    chars: str = CHARS_BLOCKS,
) -> str:
    """
    Simple grayscale ASCII art conversion.
    """
    try:
        from PIL import Image
    except ImportError:
        return ""

    try:
        img = Image.open(io.BytesIO(image_data))

        aspect_ratio = img.height / img.width
        height = int(width * aspect_ratio * 0.5)

        img = img.resize((width, height))
        img = img.convert("L")  # Grayscale

        pixels = list(img.getdata())

        lines = []
        for i in range(0, len(pixels), width):
            line = ""
            for pixel in pixels[i:i + width]:
                char_idx = int((255 - pixel) / 256 * len(chars))
                char_idx = min(char_idx, len(chars) - 1)
                line += chars[char_idx]
            lines.append(line)

        return "\n".join(lines)

    except Exception as e:
        logger.debug(f"Failed to convert image: {e}")
        return ""


def image_to_ascii_colored_simple(
    image_data: bytes,
    width: int = 40,
) -> str:
    """
    Colored ASCII using full blocks with single color per character.
    Simpler than half-blocks but still colorful.
    """
    try:
        from PIL import Image
    except ImportError:
        return ""

    try:
        img = Image.open(io.BytesIO(image_data))

        aspect_ratio = img.height / img.width
        height = int(width * aspect_ratio * 0.5)

        img = img.resize((width, height))
        img = img.convert("RGB")

        pixels = list(img.getdata())

        lines = []
        for i in range(0, len(pixels), width):
            line = ""
            for r, g, b in pixels[i:i + width]:
                hex_color = rgb_to_hex(r, g, b)
                line += f"[{hex_color}]█[/]"
            lines.append(line)

        return "\n".join(lines)

    except Exception as e:
        logger.debug(f"Failed to convert image: {e}")
        return ""


def image_to_braille(
    image_data: bytes,
    width: int = 60,
    threshold: int = 128,
) -> str:
    """
    Convert image to braille pattern art.
    Each braille character represents a 2x4 pixel grid.
    """
    try:
        from PIL import Image
    except ImportError:
        return ""

    try:
        img = Image.open(io.BytesIO(image_data))

        # Braille is 2 dots wide, 4 dots tall per character
        char_width = width
        aspect_ratio = img.height / img.width
        char_height = int(char_width * aspect_ratio * 0.5)

        pixel_width = char_width * 2
        pixel_height = char_height * 4

        img = img.resize((pixel_width, pixel_height))
        img = img.convert("L")  # Grayscale

        pixels = list(img.getdata())

        def get_pixel(x, y):
            if 0 <= x < pixel_width and 0 <= y < pixel_height:
                return pixels[y * pixel_width + x] < threshold
            return False

        # Braille dot positions
        # 1 4
        # 2 5
        # 3 6
        # 7 8
        dot_map = [
            (0, 0, 0x01), (1, 0, 0x08),
            (0, 1, 0x02), (1, 1, 0x10),
            (0, 2, 0x04), (1, 2, 0x20),
            (0, 3, 0x40), (1, 3, 0x80),
        ]

        lines = []
        for cy in range(char_height):
            line = ""
            for cx in range(char_width):
                px = cx * 2
                py = cy * 4

                code = 0x2800  # Braille base
                for dx, dy, bit in dot_map:
                    if get_pixel(px + dx, py + dy):
                        code |= bit

                line += chr(code)
            lines.append(line)

        return "\n".join(lines)

    except Exception as e:
        logger.debug(f"Failed to convert image: {e}")
        return ""


def video_thumbnail_to_ascii(
    video_id: str,
    width: int = 40,
    quality: str = "mqdefault",
    style: str = "colored_blocks",  # colored_blocks, colored_simple, blocks, braille
) -> str:
    """
    Download YouTube thumbnail and convert to ASCII art.

    Styles:
    - colored_blocks: Half-block characters with full color (best quality)
    - colored_simple: Full blocks with color
    - blocks: Grayscale block characters
    - braille: Braille dot patterns (high detail, monochrome)
    """
    image_data = download_thumbnail(video_id, quality)
    if not image_data:
        return ""

    if style == "colored_blocks":
        return image_to_ascii_blocks(image_data, width=width, colored=True)
    elif style == "colored_simple":
        return image_to_ascii_colored_simple(image_data, width=width)
    elif style == "braille":
        return image_to_braille(image_data, width=width)
    else:  # blocks
        return image_to_ascii_simple(image_data, width=width)


async def video_thumbnail_to_ascii_async(
    video_id: str,
    width: int = 40,
    quality: str = "mqdefault",
    style: str = "colored_blocks",
) -> str:
    """Async version of video_thumbnail_to_ascii."""
    image_data = await download_thumbnail_async(video_id, quality)
    if not image_data:
        return ""

    if style == "colored_blocks":
        return await asyncio.to_thread(image_to_ascii_blocks, image_data, width, True)
    elif style == "colored_simple":
        return await asyncio.to_thread(image_to_ascii_colored_simple, image_data, width)
    elif style == "braille":
        return await asyncio.to_thread(image_to_braille, image_data, width)
    else:
        return await asyncio.to_thread(image_to_ascii_simple, image_data, width)


# Cache for thumbnails
_thumbnail_cache: dict[str, str] = {}
_cache_max_size = 50


def get_cached_ascii(video_id: str) -> Optional[str]:
    """Get cached ASCII art for a video."""
    return _thumbnail_cache.get(video_id)


def cache_ascii(video_id: str, ascii_art: str) -> None:
    """Cache ASCII art for a video."""
    global _thumbnail_cache

    if len(_thumbnail_cache) >= _cache_max_size:
        oldest = next(iter(_thumbnail_cache))
        del _thumbnail_cache[oldest]

    _thumbnail_cache[video_id] = ascii_art


def clear_cache() -> None:
    """Clear the thumbnail cache."""
    global _thumbnail_cache
    _thumbnail_cache = {}


async def get_or_fetch_ascii(
    video_id: str,
    width: int = 40,
    quality: str = "mqdefault",
    style: str = "colored_blocks",
) -> str:
    """Get ASCII art from cache or fetch it."""
    cache_key = f"{video_id}_{style}_{width}"
    cached = _thumbnail_cache.get(cache_key)
    if cached:
        return cached

    ascii_art = await video_thumbnail_to_ascii_async(
        video_id,
        width=width,
        quality=quality,
        style=style,
    )

    if ascii_art:
        _thumbnail_cache[cache_key] = ascii_art

    return ascii_art
