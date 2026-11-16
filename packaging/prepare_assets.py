"""Convert the existing public logo to Windows icon sizes."""
from pathlib import Path
from PIL import Image

root = Path(__file__).resolve().parent.parent
with Image.open(root / "SnowVoice_logo.png") as image:
    image.convert("RGBA").save(root / "packaging" / "SnowVoice.ico", format="ICO",
                               sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
