---
name: hilltops-newsletter
description: Upload the monthly Hilltops VIC "What's On" newsletter to visithilltopsregion.com.au — new post, home slide, What's On button, last year's post to Draft. Use whenever the user wants to do this month's newsletter, sends a Teamwork ticket "What's On In The Hilltops Region (<Month>)", or wants the Divi JSON or the image hyperlinks from the Mailchimp newsletter. Triggers on "do the newsletter", "November newsletter", "make the JSON", "new month".
---

# Hilltops monthly newsletter

Every month Jada (Young Visitors Centre, vic@hilltops.nsw.gov.au) sends a
Teamwork ticket "Fw: What's On In The Hilltops Region (<Month YYYY>)". The ticket
always asks for **4 jobs**. Do all 4; the post alone is not the job.

1. **New post** "Newsletter <Month> <YYYY>", slug `newsletter-<month>-<yyyy>`,
   category Monthly Newsletters (233), featured image = the Thumbnail. Layout:
   Download button (the PDF) + one Divi image module per page, each linked to
   its click target in the email. Copy last month's post (content and Divi meta).
   **Post date = the 1st of that month** (Steve's rule, even if the upload is
   late): `"date": "<yyyy>-<mm>-01 09:00:00"` in `post.json` (if that time has
   not come yet, the post would be Scheduled, so use an earlier time). Every newsletter
   post was set to the 1st on 2026-11-02.
2. **Home slide.** Home (235896): the **second** `[et_pb_slider]`, slide
   `admin_title="Newsletter slide"`. Set `heading`, the `<p>` text (both from the
   ticket, word for word), `button_link` to the new post, `background_image` to
   the Hero.
3. **What's On "NEWSLETTER" button.** It is not on page 148 (that page is empty).
   It is in the Theme Builder layout **117707** "Specific Pages: What's On"
   (`et_body_layout`): `button_url="/newsletter-<month>-<yyyy>/"`.
4. **Last year's same-month post → Draft** (e.g. November 2026 job → Newsletter
   November 2025). Check that every older newsletter is Draft too: September and
   October 2025 were missed and fixed on 2026-11-02.

Then Purge All, check, and reply on the ticket with the post link.

## Where the inputs are

- **Ticket:** `https://webrenovator.teamwork.com/desk/tickets/<id>/messages`.
  Claude can read it in Chrome (Steve is logged in). Get the Mailchimp link with
  JS (walk the DOM, including shadow roots, for the "View this email in your
  browser" `<a>`): `https://mailchi.mp/hilltops/whats-on-2026-<n>?e=…`.
  The other links in the ticket are Mailchimp tracking links, which the Chrome
  tool hides. The mailchi.mp page has the real ones.
- **Files:** the same Dropbox folder every month (".2026 What's On Newsletters",
  link in the ticket): `<Month> <YYYY> - Hilltops VIC Newsletter.zip` (pages
  `1.png`…`N.png`), the `.pdf`, `<YYYY> <Month> Newsletter (Hero).jpg` (1920x1280,
  home slide) and `(Thumbnail).jpg` (600x400, featured image). Ask Steve before
  downloading. Never download "Past Newsletters". The folder page is JS-rendered:
  get each file's `/scl/fo/<folder>/<fileid>/<name>` path from the page in Chrome,
  then `curl -L "…?rlkey=<rlkey>&dl=1"`.
- **Links per page:** `scripts/build_newsletter.py` pairs email image N with
  page N. Run it with `--skip-verify` just to print the table. Then check every
  pair against `pdftotext -f N -l N <pdf> -` (business names, web addresses on
  the page) and curl every link. The last pages (What's On tables) have no link.

## Doing it without wp-admin (how it was done 2026-11-02)

The site has SFTP but no shell. Use the one-time script in
`~/Documents/GitHub/visithilltopsregion-ssh/scripts/newsletter-job.tpl.php`
(read that repo's CLAUDE.md first; OpenVPN must be on). Put a random token in
`__TOKEN__`, last month's post ID in `__PREV_ID__`, save under a random name in
`public_html/`, and stage files in `/home/vic/tmp-nl-job`. Actions
(`?t=<token>&a=`): `dump`, `get&id=`, `import&f=&title=`, `create_post`
(`post.json`), `update_page&id=&md5=` (`page-<id>.txt`; refuses if the page
changed since the dump), `draft&id=` (newsletter posts only), `set_dates`
(`dates.json`, fixes post dates; refuses future dates), `purge`, `cleanup`. After cleanup, check the script URL gives 404.

- Convert pages to JPG first (`sips -s format jpeg -s formatOptions 82`).
  Media titles `1`…`N`; the site makes `N-scaled.jpg` (1357x1920). Use the URL
  `import` returns.
- Rename Hero/Thumbnail to `Home-Slide-<YYYY>-<Month>-Newsletter.jpg` and
  `Blog-Thumbnail-<YYYY>-<Month>-Newsletter.jpg`; the PDF to
  `<Month>-<YYYY>-Hilltops-VIC-Newsletter.pdf`.
- Back up home, layout 117707 and last month's post to
  `visithilltopsregion-ssh/backups/<stamp>-newsletter-<yyyy-mm>/` before writing.
- Check after: new post 200, all linked images in order, every image URL 200
  (first requests make the Smush WebP copies, so this is slow), PDF 200; home
  shows the new heading and links to the new post; What's On button links to
  the new post; drafted posts give 404.

## Other route: Divi JSON import in wp-admin

If Steve prefers to upload in wp-admin himself, the script can build a Divi
layout-import JSON instead:

```bash
python3 scripts/build_newsletter.py \
  --month 2026-08 \
  --mailchimp "https://mailchi.mp/hilltops/whats-on-2026-18248637?e=e50981d050" \
  --pdf "https://visithilltopsregion.com.au/wp-content/uploads/2026/08/August-2026-Hilltops-VIC-Newsletter.pdf" \
  --out "Newsletter August 2026.json"
```

- Images must be uploaded first. WordPress does not convert every PNG the same
  way (September 2026: 1-10 became `.jpg`, 11-12 stayed `.png`). On 404s, check
  which name exists and pass `--names`. A 404 can also mean the upload is still
  being processed.
- Import: Divi Builder → Portability (⇅) → Import. Keep the small URL-only file
  with an empty `images` key and the PHP-style encoding (no spaces, `\/`); a
  base64 variant failed to import (August 2026).
- Flags: `--count` / `--ext` / `--names`, `--skip-verify`.
- Always show Steve the printed image → link table.
