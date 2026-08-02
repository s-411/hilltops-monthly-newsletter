#!/usr/bin/env python3
"""Build a Divi layout-import JSON for the monthly Hilltops VIC newsletter.

Reads the Mailchimp in-browser version of the newsletter to get the per-image
hyperlinks (in order), pairs them with the images already uploaded to the
WordPress media library, and writes the Divi portability JSON you drag into
the Divi Builder's Portability > Import panel.

Example:
    python3 scripts/build_newsletter.py \
        --month 2026-08 \
        --mailchimp "https://mailchi.mp/hilltops/whats-on-2026-18248637?e=e50981d050" \
        --pdf "https://visithilltopsregion.com.au/wp-content/uploads/2026/08/August-2026-Hilltops-VIC-Newsletter.pdf" \
        --out "Newsletter August 2026.json"
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import urllib.request
from typing import List, Optional, Tuple

UPLOADS_BASE = "https://visithilltopsregion.com.au/wp-content/uploads"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) newsletter-builder"

# Divi module boilerplate, copied verbatim from a known-good export so the
# imported layout matches previous months pixel for pixel.
SECTION_OPEN = (
    '[et_pb_section fb_built="1" _builder_version="4.23.2" _module_preset="default" '
    'locked="off" global_colors_info="{}"]'
    '[et_pb_row _builder_version="4.27.4" _module_preset="default" width="100%" '
    'width_tablet="100%" width_phone="95%" width_last_edited="on|phone" global_colors_info="{}"]'
    '[et_pb_column type="4_4" _builder_version="4.27.3" _module_preset="default" '
    'global_colors_info="{}"]'
)
SECTION_CLOSE = "[/et_pb_column][/et_pb_row][/et_pb_section]"

BUTTON = (
    '[et_pb_button button_url="{pdf}" url_new_window="on" button_text="Download" '
    'button_alignment="center" disabled_on="off|off|off" admin_label="Button" '
    '_builder_version="4.27.6" _module_preset="default" custom_button="on" '
    'button_text_color="#FFFFFF" button_bg_color="#C1C99A" button_border_width="0px" '
    'button_icon="&#x35;||divi||400" custom_padding="7px||7px||true|false" '
    'custom_css_main_element="width: 250px;||text-align: center;" locked="off" '
    'global_colors_info="{{}}"][/et_pb_button]'
)

IMAGE = (
    '[et_pb_image src="{src}" title_text="{title}"{url_attr} url_new_window="on" '
    'align="center" admin_label="{label}" _builder_version="4.27.6" '
    '_module_preset="default" module_alignment="center" '
    'custom_padding="2em||||false|false" global_colors_info="{{}}"][/et_pb_image]'
)

PRESETS = {
    "et_pb_row": {
        "presets": {
            "_initial": {
                "name": "Row Preset 1",
                "version": "4.25.0",
                "settings": {"width_last_edited": "off|desktop", "width_tablet": "90%"},
            }
        },
        "default": "_initial",
    }
}

GLOBAL_COLORS = [
    ["gcid-primary-color", {"color": "#000000", "active": "yes"}],
    ["gcid-secondary-color", {"color": "#2ea3f2", "active": "yes"}],
    ["gcid-heading-color", {"color": "#222222", "active": "yes"}],
    ["gcid-body-color", {"color": "#2c2b2b", "active": "yes"}],
    ["gcid-4dccef5c-a04c-4e7c-abbe-b1e880c58010", {"color": "#082125", "active": "yes"}],
    ["gcid-f743be1f-46bf-4685-bc55-7e8b347eb98d", {"color": "#d2d0bb", "active": "yes"}],
    ["gcid-0bde52ea-11f0-4367-a196-10c34de3041d", {"color": "#22484f", "active": "yes"}],
    ["gcid-9464c34f-f9ff-43eb-9668-c958662e33fc", {"color": "#f5ede7", "active": "yes"}],
    ["gcid-0b738e94-8a5e-4e5c-8969-81d151b757fa", {"color": "#ca5500", "active": "yes"}],
    ["gcid-0a41bebc-0107-48f7-8173-6190cad71074", {"color": "#dcff77", "active": "yes"}],
    ["gcid-aa58ace8-f27f-4d3e-bff4-606cd9606937", {"color": "#acade8", "active": "yes"}],
    ["gcid-995ea536-d942-449e-b40e-0d7d5e4aa608", {"color": "#666666", "active": "yes"}],
    ["gcid-fb7185f0-febc-426c-87a9-b6e9798849ab", {"color": "#8c8eff", "active": "yes"}],
]


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


def head_status(url: str) -> int:
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status
    except urllib.error.HTTPError as exc:
        return exc.code
    except Exception:
        return 0


def extract_links(page_html: str) -> List[Tuple[str, Optional[str]]]:
    """Return (image src, wrapping href or None) for every <img> in document order."""
    results: List[Tuple[str, Optional[str]]] = []
    for match in re.finditer(r"<img[^>]*>", page_html, re.IGNORECASE):
        tag = match.group(0)
        src = re.search(r'src="([^"]+)"', tag, re.IGNORECASE)
        if not src:
            continue
        href = None
        before = page_html[: match.start()]
        anchor_start = before.rfind("<a ")
        if anchor_start != -1 and "</a>" not in page_html[anchor_start : match.start()]:
            found = re.search(r'href="([^"]+)"', page_html[anchor_start : anchor_start + 2000])
            if found:
                href = html.unescape(found.group(1)).strip()
        results.append((html.unescape(src.group(1)), href))
    return results


def is_content_image(src: str, href: Optional[str]) -> bool:
    """Filter out Mailchimp chrome (tracking pixels, social icons, footer badges)."""
    lowered = src.lower()
    if "mcusercontent.com" not in lowered:
        return False
    if re.search(r"\b(spacer|pixel|open\.php)\b", lowered):
        return False
    return True


def build_layout(images: List[Tuple[str, Optional[str]]], pdf_url: str) -> str:
    parts = [SECTION_OPEN, BUTTON.format(pdf=pdf_url)]
    for index, (src, href) in enumerate(images, start=1):
        title = src.rsplit("/", 1)[-1].rsplit(".", 1)[0]
        url_attr = f' url="{href}"' if href else ""
        parts.append(
            IMAGE.format(src=src, title=title, url_attr=url_attr, label=str(index))
        )
    parts.append(SECTION_CLOSE)
    return "".join(parts)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--month", required=True, help="Upload month as YYYY-MM, e.g. 2026-08")
    parser.add_argument("--mailchimp", required=True, help="Mailchimp 'view in browser' URL for this month")
    parser.add_argument("--pdf", required=True, help="URL of the uploaded newsletter PDF")
    parser.add_argument("--out", required=True, help="Output JSON path")
    parser.add_argument("--count", type=int, default=0, help="Expected image count (0 = however many the email has)")
    parser.add_argument("--ext", default="jpg", help="Extension of the uploaded images (default: jpg)")
    parser.add_argument("--names", default="", help="Comma-separated image filenames, overrides the 1..N pattern")
    parser.add_argument("--uploads-base", default=UPLOADS_BASE, help="WordPress uploads base URL")
    parser.add_argument("--layout-id", default="241358", help="Divi layout key inside the JSON")
    parser.add_argument("--skip-verify", action="store_true", help="Skip HEAD checks on the image and PDF URLs")
    args = parser.parse_args()

    if not re.fullmatch(r"\d{4}-\d{2}", args.month):
        parser.error("--month must look like 2026-08")
    year, month = args.month.split("-")
    base = f"{args.uploads_base.rstrip('/')}/{year}/{month}"

    print(f"Fetching {args.mailchimp}", file=sys.stderr)
    page = fetch(args.mailchimp).decode("utf-8", errors="replace")
    found = [(src, href) for src, href in extract_links(page) if is_content_image(src, href)]
    if not found:
        print("ERROR: no content images found in the Mailchimp page", file=sys.stderr)
        return 1
    print(f"Found {len(found)} images in the email, {sum(1 for _, h in found if h)} with links", file=sys.stderr)

    if args.names:
        filenames = [n.strip() for n in args.names.split(",") if n.strip()]
    else:
        count = args.count or len(found)
        filenames = [f"{i}.{args.ext.lstrip('.')}" for i in range(1, count + 1)]

    if len(filenames) != len(found):
        print(
            f"WARNING: {len(filenames)} image files vs {len(found)} images in the email. "
            "Links are matched by position, so check the pairing below.",
            file=sys.stderr,
        )

    pairs: List[Tuple[str, Optional[str]]] = []
    for i, name in enumerate(filenames):
        href = found[i][1] if i < len(found) else None
        pairs.append((f"{base}/{name}", href))

    problems = 0
    if not args.skip_verify:
        for src, _ in pairs:
            status = head_status(src)
            if status != 200:
                print(f"WARNING: {src} returned HTTP {status}", file=sys.stderr)
                problems += 1
        pdf_status = head_status(args.pdf)
        if pdf_status != 200:
            print(f"WARNING: PDF {args.pdf} returned HTTP {pdf_status}", file=sys.stderr)
            problems += 1

    # "images" stays empty on purpose. It is where Divi puts base64 copies of
    # the artwork so a cross-site import can re-upload it. These images are
    # already in this site's media library, so an empty map keeps the file at
    # a few KB and imports cleanly.
    payload = {
        "context": "et_builder",
        "data": {args.layout_id: build_layout(pairs, args.pdf)},
        "presets": PRESETS,
        "global_colors": GLOBAL_COLORS,
        "images": {},
        "thumbnails": [],
    }

    # Serialise the way PHP's json_encode does, matching Divi's own exports:
    # no whitespace between tokens, every forward slash escaped. JSON has no
    # bare "/" outside of strings, so the blanket replace is safe. This exact
    # encoding is what imported successfully in August 2026.
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("/", "\\/")
    with open(args.out, "w", encoding="utf-8") as handle:
        handle.write(encoded)

    print("", file=sys.stderr)
    for i, (src, href) in enumerate(pairs, start=1):
        print(f"  {i:>2}. {src.rsplit('/', 1)[-1]:<12} -> {href or '(no link)'}", file=sys.stderr)
    print(f"\nWrote {args.out}", file=sys.stderr)
    if problems:
        print(f"{problems} URL(s) did not return 200 — fix those before importing.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
