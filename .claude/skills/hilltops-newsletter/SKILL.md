---
name: hilltops-newsletter
description: Build the monthly Hilltops VIC newsletter Divi import JSON. Use whenever the user wants to create this month's newsletter, generate the Divi/WordPress JSON, or pull the image hyperlinks out of the Mailchimp newsletter. Triggers on "do the newsletter", "August newsletter", "make the JSON", "new month".
---

# Hilltops monthly newsletter

Turns the month's Mailchimp campaign plus the images already uploaded to
WordPress into a Divi layout-import JSON. The whole job is one script run.

## What you need from the user

1. **Mailchimp "view in browser" URL** for this month's campaign
   (e.g. `https://mailchi.mp/hilltops/whats-on-2026-18248637?e=e50981d050`).
   This is where the per-image hyperlinks come from — never ask the user to
   copy them out by hand.
2. **Upload month** as `YYYY-MM` — the WordPress uploads folder
   (`/wp-content/uploads/2026/08/`).
3. **PDF URL** for the newsletter download button. WordPress sanitises the
   upload filename, so `August 2026 - Hilltops VIC Newsletter.pdf` becomes
   `.../2026/08/August-2026-Hilltops-VIC-Newsletter.pdf`. Guess it from that
   pattern and let the script's HEAD check confirm it.

The images must already be uploaded to WordPress before running. They land as
`1.jpg` … `12.jpg` (WordPress converts the source PNGs). Count and extension
are both overridable.

## Run it

```bash
python3 scripts/build_newsletter.py \
  --month 2026-08 \
  --mailchimp "https://mailchi.mp/hilltops/whats-on-2026-18248637?e=e50981d050" \
  --pdf "https://visithilltopsregion.com.au/wp-content/uploads/2026/08/August-2026-Hilltops-VIC-Newsletter.pdf" \
  --out "Newsletter August 2026.json"
```

The script:

- fetches the Mailchimp page and pulls every content `<img>` **in document
  order** along with the `<a href>` wrapping it (unwrapped images get no link);
- pairs image *N* in the email with `N.jpg` in the uploads folder — **position
  is the only thing tying links to images**;
- HEAD-checks every image URL and the PDF URL, warning on anything that isn't
  200;
- writes the Divi JSON and prints the image→link table.

Always show the user that printed table. It is the one thing worth eyeballing.

Useful flags: `--count` / `--ext` / `--names` when the images aren't a plain
`1..N.jpg` run, `--skip-verify` to skip the HTTP checks.

Produce exactly one file per month, in this format. Do not build variants.

## Importing

Divi Builder → Portability (the ⇅ icon) → Import → upload the JSON.

The output is ~7 KB and just references the live image URLs. Its `images` key
is deliberately empty: that key exists so a cross-site import can re-upload
base64 copies of the artwork, but these images are already in this site's own
media library, so there is nothing to carry.

**This was confirmed against the live site in August 2026.** The small
URL-only file imported correctly; a fat variant with base64-embedded images
failed to import at all. Do not reintroduce embedded images — the old 5 MB
exports in this repo are historical, not a target to match.

The script also writes the JSON the way PHP's `json_encode` does — no spaces
between tokens, every `/` escaped as `\/` — which is how Divi writes its own
exports. That is the encoding that imported cleanly, so leave it alone.

## Layout notes

Every month is the same single section: one Download button, then N full-width
image modules stacked with `2em` top padding. The boilerplate lives in
`scripts/build_newsletter.py` (`SECTION_OPEN`, `BUTTON`, `IMAGE`,
`GLOBAL_COLORS`) copied verbatim from a known-good export. If the client
changes the design, update those constants rather than hand-editing output.

The trailing images (contact details, the What's On table) usually have no
hyperlink — that's expected, not a bug, and it comes straight from how the
email was built.
