"""
demo.py — Standalone demo of the CAPTCHA-solving pipeline.

This script demonstrates the core logic *without* needing Selenium or a live
CAPTCHA page. It:
  1. Generates a synthetic 3x3 CAPTCHA-style grid image from freely usable
     placeholder images (or solid colour tiles as a fallback).
  2. Splits the grid into individual tiles (reusing src/decaptcha logic).
  3. Sends each tile to a local Ollama instance running LLaVA for classification.
  4. Prints the per-tile predictions in a visual grid layout.

Prerequisites:
  - Ollama running locally:  ollama serve
  - LLaVA model pulled:      ollama pull llava

Usage:
  python demo.py                      # uses generated colour-block grid
  python demo.py path/to/grid.jpg     # uses a real CAPTCHA grid image
  python demo.py --offline             # skip Ollama, just test image splitting
"""

import sys
import os
import base64
import io
import logging
import textwrap

import requests
from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------------------
# Configuration (matches src/decaptcha.py defaults)
# ---------------------------------------------------------------------------
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llava"
PROMPT_TEMPLATE = "Respond with 1 if image has a {target}, else 0."
API_TIMEOUT = 200

GRID_SIZE = 3
TILE_PX = 150  # pixels per tile in the synthetic image
TARGET_LABEL = "traffic light"

# ---------------------------------------------------------------------------
# Synthetic image generation
# ---------------------------------------------------------------------------

# Layout:  we paint a 3x3 grid where some tiles represent the "target"
# (drawn in bright red/yellow/green to mimic a traffic light pattern)
# and the rest are neutral (blue sky / grey road).
TILE_COLOURS = [
    "#87CEEB",  # sky
    "#FF4444",  # traffic light (red)
    "#87CEEB",  # sky
    "#808080",  # road
    "#44DD44",  # traffic light (green)
    "#808080",  # road
    "#808080",  # road
    "#FFCC00",  # traffic light (yellow)
    "#87CEEB",  # sky
]

# Ground-truth: which tiles are the "target"
GROUND_TRUTH = [False, True, False,
                False, True, False,
                False, True, False]


def _generate_synthetic_grid(grid_size: int, tile_px: int, save_path: str) -> str:
    """Create a simple colour-block grid image and save it to disk."""
    img = Image.new("RGB", (grid_size * tile_px, grid_size * tile_px))
    draw = ImageDraw.Draw(img)
    for idx, colour in enumerate(TILE_COLOURS[:grid_size * grid_size]):
        row, col = divmod(idx, grid_size)
        x0, y0 = col * tile_px, row * tile_px
        x1, y1 = x0 + tile_px, y0 + tile_px
        draw.rectangle([x0, y0, x1, y1], fill=colour)
        # Draw a label inside each tile
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
        except (IOError, OSError):
            font = ImageFont.load_default()
        label = f"tile {idx}"
        draw.text((x0 + 8, y0 + 8), label, fill="black", font=font)
    img.save(save_path)
    return save_path


# ---------------------------------------------------------------------------
# Image splitting (mirrors src/decaptcha._split_and_encode_image)
# ---------------------------------------------------------------------------

def split_and_encode(image_path: str, grid_size: int) -> list[str]:
    """Split a grid image into tiles and return base64-encoded PNGs."""
    with Image.open(image_path) as img:
        width, height = img.size
        tile_size = min(width, height) // grid_size
        parts = []
        for i in range(grid_size):
            for j in range(grid_size):
                box = (j * tile_size, i * tile_size,
                       j * tile_size + tile_size, i * tile_size + tile_size)
                tile = img.crop(box)
                buf = io.BytesIO()
                tile.save(buf, format="PNG")
                parts.append(base64.b64encode(buf.getvalue()).decode("utf-8"))
    return parts


# ---------------------------------------------------------------------------
# Ollama API call (mirrors src/decaptcha._make_vLLM_API_call)
# ---------------------------------------------------------------------------

def classify_tile(target: str, b64_image: str) -> str:
    """Send a single tile to Ollama/LLaVA and return the raw response text."""
    payload = {
        "model": MODEL,
        "prompt": PROMPT_TEMPLATE.format(target=target),
        "stream": False,
        "images": [b64_image],
    }
    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=API_TIMEOUT)
    except requests.ConnectionError:
        return "ERR:connection_refused"
    if resp.status_code == 200:
        return resp.json()["response"].strip()
    return f"ERR:{resp.status_code}"


# ---------------------------------------------------------------------------
# Pretty-print helpers
# ---------------------------------------------------------------------------

def _print_grid(values: list, grid_size: int, title: str):
    print(f"\n  {title}")
    print("  " + "-" * (grid_size * 8 + 1))
    for row in range(grid_size):
        cells = []
        for col in range(grid_size):
            v = values[row * grid_size + col]
            cells.append(f" {str(v):^6}")
        print("  |" + "|".join(cells) + "|")
    print("  " + "-" * (grid_size * 8 + 1))


# ---------------------------------------------------------------------------
# Main demo flow
# ---------------------------------------------------------------------------

def main():
    offline = "--offline" in sys.argv
    custom_image = None
    for arg in sys.argv[1:]:
        if arg != "--offline":
            custom_image = arg

    print(textwrap.dedent(f"""\
    ╔══════════════════════════════════════════════════════╗
    ║          CAPTCHA-Solving Agent — Demo               ║
    ╠══════════════════════════════════════════════════════╣
    ║  Target class : {TARGET_LABEL:<37}║
    ║  Grid size    : {GRID_SIZE}x{GRID_SIZE:<35}║
    ║  Model        : {MODEL:<37}║
    ║  Ollama URL   : {OLLAMA_URL:<37}║
    ║  Mode         : {"OFFLINE (no Ollama)" if offline else "LIVE (calls Ollama)":<37}║
    ╚══════════════════════════════════════════════════════╝
    """))

    # --- Step 1: Get or generate grid image ---
    if custom_image:
        image_path = custom_image
        print(f"  [1/3] Using provided image: {image_path}")
    else:
        os.makedirs("temp", exist_ok=True)
        image_path = _generate_synthetic_grid(GRID_SIZE, TILE_PX, "temp/demo_grid.png")
        print(f"  [1/3] Generated synthetic grid image -> {image_path}")

    # --- Step 2: Split into tiles ---
    tiles = split_and_encode(image_path, GRID_SIZE)
    print(f"  [2/3] Split into {len(tiles)} tiles ({GRID_SIZE}x{GRID_SIZE})")

    # Show tile sizes
    for idx, t in enumerate(tiles):
        kb = len(t) * 3 / 4 / 1024  # approx decoded size in KB
        print(f"         tile {idx}: ~{kb:.1f} KB (base64)")

    # --- Step 3: Classify each tile ---
    if offline:
        print(f"  [3/3] Offline mode — skipping Ollama classification")
        print("\n  Image splitting works correctly. To run the full pipeline:")
        print("    1. Start Ollama:   ollama serve")
        print("    2. Pull model:     ollama pull llava")
        print("    3. Run:            python demo.py")
        return

    print(f"  [3/3] Classifying tiles via Ollama ({MODEL})...")
    print(f"         Prompt: \"{PROMPT_TEMPLATE.format(target=TARGET_LABEL)}\"")
    print()

    predictions = []
    for idx, tile in enumerate(tiles):
        raw = classify_tile(TARGET_LABEL, tile)
        pred = None
        if raw.startswith("ERR:"):
            print(f"         tile {idx}: API error -> {raw}")
            pred = "ERR"
        else:
            # LLaVA sometimes returns verbose answers; extract leading 0/1
            first_char = raw[0] if raw else "?"
            if first_char in ("0", "1"):
                pred = bool(int(first_char))
            else:
                pred = f"?({raw[:20]})"
            print(f"         tile {idx}: raw=\"{raw[:40]}\" -> {pred}")
        predictions.append(pred)

    # --- Results ---
    _print_grid(predictions, GRID_SIZE, "Predictions")

    if not custom_image:
        _print_grid(GROUND_TRUTH, GRID_SIZE, "Ground Truth")
        correct = sum(1 for p, g in zip(predictions, GROUND_TRUTH)
                      if p == g)
        total = len(GROUND_TRUTH)
        print(f"\n  Accuracy: {correct}/{total} ({100*correct/total:.0f}%)")

    print("\n  Done.")


if __name__ == "__main__":
    main()
