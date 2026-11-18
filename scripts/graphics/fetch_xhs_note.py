#!/usr/bin/env python3
"""Download every image of a Xiaohongshu image note (图文笔记) for the graphic design section.

Run with the XHS-Downloader virtualenv, which provides its dependencies:

    ~/.local/share/codex-tools/XHS-Downloader/.venv/bin/python \
        scripts/graphics/fetch_xhs_note.py "<share link or xhslink.cn short link>" <out-dir>

Images land in <out-dir>/download/ as PNG (the note's full resolution, about 1262 px wide),
together with a Markdown file holding the title, author and description. Keep <out-dir>
outside the repository (for example ~/.local/share/codex-data/xhs-graphic/<batch>): these are
third-party originals; only the cropped, credited excerpts go into assets/graphics/.
"""
import asyncio
import http.client
import os
import sys
from pathlib import Path
from urllib.parse import urlsplit

REPO = Path(os.environ.get("XHS_DOWNLOADER_ROOT", "~/.local/share/codex-tools/XHS-Downloader")).expanduser()
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"


def resolve(url: str) -> str:
    """Follow xhslink.cn redirects without loading the note page itself; drop tracking params."""
    for _ in range(5):
        parts = urlsplit(url)
        if "xhslink" not in parts.netloc:
            break
        conn = http.client.HTTPSConnection(parts.netloc, timeout=20)
        conn.request("GET", parts.path + ("?" + parts.query if parts.query else ""), headers={"User-Agent": UA})
        resp = conn.getresponse()
        location = resp.getheader("Location")
        conn.close()
        if not location:
            break
        url = location
    return url.split("&shareRedId")[0]


async def download(url: str, out: Path):
    sys.path.insert(0, str(REPO))
    from source import XHS  # provided by XHS-Downloader
    async with XHS(work_path=str(out), folder_name="download", folder_mode=False, author_archive=False,
                   note_format="md", record_data=True, download_record=False, timeout=20, max_retry=3,
                   cookie=os.environ.get("XHS_COOKIE", ""), proxy=os.environ.get("XHS_PROXY") or None,
                   video_download=False, image_download=True, live_download=False, image_format="PNG") as xhs:
        return await xhs.extract(url, download=True, check_record=False)


def main():
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    url, out = resolve(sys.argv[1]), Path(sys.argv[2]).expanduser()
    out.mkdir(parents=True, exist_ok=True)
    result = asyncio.run(download(url, out))
    images = sorted((out / "download").glob("*.png"))
    if not images:
        raise SystemExit("No images downloaded. Use a fresh share link (it carries xsec_token) or set XHS_COOKIE.")
    meta = result[0] if result else {}
    print(f"Note: {meta.get('作品标题', '?')} · {meta.get('作者昵称', '?')} · {meta.get('发布时间', '?')}")
    print(f"Link: {meta.get('作品链接', url).split('?')[0]}")
    print(f"{len(images)} images in {out / 'download'}")


if __name__ == "__main__":
    main()
