"""Keep distribution metadata and supplied licenses beside the frozen application."""
from importlib.metadata import distributions
import json
from pathlib import Path
import sys

output = Path("dist/SnowVoice/THIRD_PARTY")
output.mkdir(parents=True, exist_ok=True)
manifest = []
for dist in sorted(distributions(), key=lambda d: d.metadata["Name"].lower()):
    name = dist.metadata["Name"]
    manifest.append({"name": name, "version": dist.version,
                     "license": dist.metadata.get("License-Expression") or dist.metadata.get("License", "See metadata")})
    folder = output / name
    folder.mkdir(exist_ok=True)
    (folder / "METADATA.txt").write_text(dist.read_text("METADATA") or "", encoding="utf-8")
    for file in dist.files or []:
        if any(word in str(file).lower() for word in ("license", "copying", "notice")) and ".dist-info/" in str(file):
            source = Path(dist.locate_file(file))
            if source.is_file():
                relative = str(file).split(".dist-info/", 1)[1]
                target = folder / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(source.read_bytes())
(output / "manifest.json").write_text(json.dumps({"python": sys.version, "packages": manifest}, indent=2), encoding="utf-8")
python_license = Path(sys.base_prefix) / "LICENSE.txt"
if python_license.exists():
    (output / "PYTHON-LICENSE.txt").write_bytes(python_license.read_bytes())
