"""Restore the original BVB News Desk v3.3 front-end verbatim.

The source snapshot is the user's original Chinese v3.3 FIXED bundle,
packed as an LZMA-compressed TAR split into nine plain-text parts to
keep GitHub's UTF-8 file API safe. Never replace it with a mock preview.
"""
from __future__ import annotations
import base64
import hashlib
import io
import lzma
from pathlib import Path
import tarfile

SOURCE_DIR = Path(__file__).resolve().parent / "bvb_v33_pack"
COUNT = 9
ARCHIVE_SHA256 = "18f3dc83bb3a8abba542dc5bdca230a1d8fe01615ea2a2478811c503066a49bf"
EXPECTED_FILES = frozenset(("index.html", "styles.css", "app.js", "materials-data.js"))


def restore_news_v33(destination: Path) -> dict[str, str]:
    parts = [(SOURCE_DIR / f"part{index:02d}.txt").read_text(encoding="ascii").strip()
             for index in range(1, COUNT + 1)]
    compressed = base64.b64decode("".join(parts), validate=True)
    checksum = hashlib.sha256(compressed).hexdigest()
    if checksum != ARCHIVE_SHA256:
        raise ValueError("Original BVB v3.3 archive checksum mismatch: " + checksum)
    payload = lzma.decompress(compressed)
    files: dict[str, bytes] = {}
    with tarfile.open(fileobj=io.BytesIO(payload), mode="r:") as archive:
        for member in archive.getmembers():
            if not member.isfile() or member.name not in EXPECTED_FILES:
                raise ValueError("Unexpected BVB archive member: " + member.name)
            if member.name in files:
                raise ValueError("Duplicate BVB archive member")
            content = archive.extractfile(member)
            if content is None or member.size > 200_000:
                raise ValueError("Invalid BVB archive member")
            files[member.name] = content.read()
    if frozenset(files) != EXPECTED_FILES:
        raise ValueError("Incomplete BVB source snapshot")
    if "v3.3" not in files["index.html"].decode("utf-8-sig"):
        raise ValueError("Unexpected BVB version")
    if "资料包编辑与发布审核" not in files["index.html"].decode("utf-8-sig"):
        raise ValueError("Original review workflow missing")

    destination.mkdir(parents=True, exist_ok=True)
    for filename, content in files.items():
        (destination / filename).write_bytes(content)
    return {name: hashlib.sha256(data).hexdigest() for name, data in files.items()}


if __name__ == "__main__":
    out = Path(__file__).resolve().parents[1] / "build" / "bvb-news-v33"
    for name, digest in restore_news_v33(out).items():
        print(name, digest)
