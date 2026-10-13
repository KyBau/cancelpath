"""Regenerate icon.png (512x512) — the binary isn't committed via the API. Requires Pillow."""
from PIL import Image, ImageDraw
im = Image.new("RGB", (512, 512), "#0F766E"); d = ImageDraw.Draw(im)
d.rounded_rectangle((96, 96, 416, 416), radius=64, outline="white", width=28)
d.line((176, 256, 240, 320), fill="white", width=36); d.line((240, 320, 348, 196), fill="white", width=36)
im.save("icon.png")
