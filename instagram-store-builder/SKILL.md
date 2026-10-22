---
name: instagram-store-builder
description: Marketing pipeline that turns one Instagram shop from the leads Excel file into a ready demo store on PRODUCTION safqi.app — picks the highest-priority pending lead, studies the Instagram profile in Chrome, creates the tenant + owner in /central/tenants ({username}@safqi.app + generated password saved back to the Excel), enters the store as the merchant, sets logo (Instagram profile picture) + basic info, imports at least 10 products built from the posts, and switches the theme when the shop's niche calls for it. Triggers — "build store from instagram", "generate tenant from excel", "marketing store", "demo store for lead", "متجر من انستقرام", "أنشئ متجر للعميل".
---

# Instagram → Safqi demo store (one lead per run)

**One run = one lead.** Never batch several profiles in one run — Instagram
rate-limits fast browsing and can flag the user's account. To do more, the user
runs the skill again (or `/loop`s it).

Everything happens in the user's **real Chrome** (load the claude-in-chrome tools
in ONE ToolSearch call, include `javascript_tool`, `file_upload`, `get_page_text`,
`find`). They are already logged in to Instagram and to `https://safqi.app/central`.

**Golden rules**
- This writes to **production**. Never delete, overwrite or edit an existing
  tenant/user. If the slug or email already exists → stop, mark the row
  `status=skipped` with the reason, report.
- The password is written to the Excel **before** the tenant form is submitted,
  so a crash can never lose a created account's password.
- Instagram is **read-only**: no follow, like, comment, DM, or story view. Scroll
  at most ~4 screens of the grid.
- The store stays **hidden** (`maintenance_mode = true`) unless the user said in
  this conversation to publish it. These are real businesses' brands — the store
  is a demo to show the merchant, not a live shop under their name.
- All store copy (name, descriptions, categories, products) is **Arabic**. The
  brand is written **سافكي** — never صفقي.
- Never assign a plan, extend a trial, or touch billing without the user's OK.

Paths below: `SKILL_DIR=.claude/skills/instagram-store-builder`,
`SCRATCH` = the session scratchpad directory (download images there, in a
per-lead subfolder).

---

## 1. Pick the lead (Excel)

Ask for the Excel path if the user didn't give one (remember it for the session).
Make sure the file is **not open in Excel** before any write.

```bash
python3 $SKILL_DIR/scripts/leads.py list "/path/leads.xlsx"            # pending rows as JSON
python3 $SKILL_DIR/scripts/leads.py update "/path/leads.xlsx" 7 status=in_progress
```

`update` creates any missing header column, so these columns appear on first use:
`status, slug, email, password, store_url, admin_url, theme, products_count, notes, created_at`.

The workbook may be a Numbers export whose first sheet is an "Export Summary" —
pass `--sheet "<name>"` to both commands (inspect the sheet names first). Our
`status` column is separate from any outreach column like `حالة التواصل`.
Back up the file to `SCRATCH` before the first write.

Choosing the row:
1. If there is a priority-like column (`priority`, `الأولوية`, `score`…) use it —
   a numeric column means **1 = highest** unless the values clearly say otherwise
   (`high/عالية/A`). Ask once if it's genuinely ambiguous.
2. Ties / no column → prefer rows with more info (phone, city, category), then
   top-to-bottom order.
3. Skip rows with no Instagram username.

Mark the row `status=in_progress` immediately.

## 2. Study the Instagram profile

Navigate to `https://www.instagram.com/{username}/` in a **new tab**. Normalize
the username first (strip `@`, full URLs, query strings).

- Profile missing / private / zero posts → `status=skipped notes=<reason>`, stop.
- Read: display name, bio, category label, phone/WhatsApp, city, link in bio,
  follower count. Use `get_page_text` for text — cheaper than screenshots.
- Take one screenshot of the grid to *judge* the images (visual quality matters:
  clear single product, good light, no heavy text overlays, no people's faces
  as the main subject when avoidable).

Pull real image URLs from the DOM (screenshots are too low-res to use):

```js
// profile picture — the largest candidate
const pic = [...document.querySelectorAll('header img')].map(i => i.currentSrc || i.src)[0];
// post grid: link + best srcset entry + alt text (IG's alt often describes the product)
const posts = [...document.querySelectorAll('a[href*="/p/"], a[href*="/reel/"]')].map(a => {
  const img = a.querySelector('img');
  if (!img) return null;
  const best = (img.srcset || '').split(',').map(s => s.trim().split(' '))
    .sort((x, y) => parseInt(y[1]) - parseInt(x[1]))[0]?.[0] || img.src;
  return { href: a.href, url: best, alt: img.alt };
}).filter(Boolean);
JSON.stringify({ pic, posts: posts.slice(0, 40) });
```

For posts that look like products, open the post (or read the `alt`) to get the
caption — that's where names, prices, sizes and colors live. Open only as many
posts as needed (~10–15), with a short pause between them.

Build a **store brief** before creating anything:
- `name` — Arabic store name (from display name; transliterate a Latin brand name
  only if the shop itself uses Arabic, otherwise keep the brand as-is)
- `niche` — e.g. عبايات، عطور، أحذية، إلكترونيات، حلويات…
- `phone` / `whatsapp`, `city`, `instagram_url`
- `products[]` — **≥ 10**, each with `name`, `short_description`, `description`
  (2–4 Arabic sentences, sales tone, no invented claims like "أصلي ١٠٠٪"),
  `price`, optional `sale_price`, `category` (`أب > ابن` path, 2–5 categories
  total), `images[]` (1–4 URLs of the same product).
  - Price from the caption when present. Otherwise estimate a realistic price in
    the store currency and add `أسعار تقديرية` to the row's `notes`.
  - Fewer than 10 real product posts → reuse different angles/colors as separate
    products only if they are genuinely different items; otherwise stop at what
    exists, note it, and tell the user. Never fake products the shop doesn't sell.
- `theme` — see §6.

Download the profile picture locally (IG CDN URLs are signed and expire):
```bash
mkdir -p "$SCRATCH/leads/{slug}" && curl -sL "<pic url>" -o "$SCRATCH/leads/{slug}/logo.jpg"
```

## 3. Create the tenant (central)

Derive identifiers from the username:
- `slug` = lowercase, `.` and `_` → `-`, strip anything not `[a-z0-9-]`, trim
  `-` (DNS-safe — it becomes `{slug}.safqi.app`).
- `email` = `{slug}@safqi.app`
- `password` = 12 random chars, letters + digits:
  `python3 -c "import secrets,string;print(''.join(secrets.choice(string.ascii_letters+string.digits) for _ in range(12)))"`

**Write `slug`, `email`, `password` to the Excel row now.**

Open `https://safqi.app/central/tenants` in Chrome. Search the list for the slug
first; if it exists → skip (golden rule). Then create from the page context
(same-origin, the session cookie + XSRF cookie authenticate it):

```js
const xsrf = decodeURIComponent(document.cookie.match(/XSRF-TOKEN=([^;]+)/)[1]);
const res = await fetch('/central/tenants', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json', 'Accept': 'application/json', 'X-XSRF-TOKEN': xsrf, 'X-Requested-With': 'XMLHttpRequest' },
  body: JSON.stringify({ name, slug, phone, location: city,
    owner_name: name, owner_email: email, owner_password: password }),
});
res.status + ' ' + (await res.text()).slice(0, 300);
```

`central.tenants.store` validates `name`, `slug` (unique), `phone`, `location`,
and the owner trio (all-or-none, email unique, password ≥ 8). A 422 lists the
field errors — fix and retry once; a 2xx/redirect means created. New tenants are
created `is_active = true` with `maintenance_mode = true`.

(Falling back to the UI form at `/central/tenants/create` is fine if the JSON
call misbehaves — fill it with `find` + `form_input`.)

Find the new tenant's id (reload the list / search the slug and read the edit
link `/central/tenants/{id}/edit`).

## 4. Enter as the merchant

```js
const xsrf = decodeURIComponent(document.cookie.match(/XSRF-TOKEN=([^;]+)/)[1]);
const r = await fetch(`/central/tenants/${id}/impersonate`, { method: 'POST',
  headers: { 'Accept': 'application/json', 'X-XSRF-TOKEN': xsrf, 'X-Requested-With': 'XMLHttpRequest' } });
(await r.json()).url;
```

Navigate a **new tab** to the returned one-time `url` (it lands on the
impersonation host, `admin.safqi.app`, logged in as the owner). Every admin call
below runs from a page on that host, with the same XSRF-cookie pattern.

Read the page props when you need server data:
`JSON.parse(document.getElementById('app').dataset.page).props`.

## 5. Basic info + logo

A brand-new store is redirected to the one-time setup wizard
(`/admin/setup`, `admin.setup.store`). Submit it as multipart:

| field | value |
|---|---|
| `currency` | keep the store's default — read it from the setup page props; never guess |
| `maintenance_mode` | `1` (hidden) unless the user said publish |
| `logo` | the profile picture file (image, ≤ 2 MB) |
| `instagram_url` | `https://instagram.com/{username}` |
| `whatsapp_number` | if found |
| `tour` | `0` |

Getting the logo file into the browser, in order of preference:
1. `fetch(picUrl).then(r => r.blob())` from the admin page (works when the IG
   CDN sends CORS headers), then `fd.append('logo', blob, 'logo.jpg')`.
2. `file_upload` the local `logo.jpg` onto the setup page's logo `<input type=file>`
   and submit the wizard through the UI.
3. Inline base64 (the profile pic is small): `base64 -i logo.jpg` → in JS
   `new Blob([Uint8Array.from(atob(b64), c => c.charCodeAt(0))], {type:'image/jpeg'})`.

If the wizard was already completed, use `POST /admin/settings`
(`admin.settings.update`: `name` required, `phone`, `location`, `logo`) instead.
Verify: the response / reloaded props show a `full_logo_url`.

## 6. Products (≥ 10) — one CSV import

Use the `standard` import dialect (`admin.products.import`) — one request creates
the products, auto-creates the category paths, and the **server downloads the
image URLs**. Build the CSV in JS and post it:

Columns (header row exactly): `Name, Slug, SKU, Brand, Categories, Price, Sale Price, Cost Price, Weight, Short Description, Description, Tags, Active, Digital, Quantity, Images, Variants`
- `Categories` — `أب > ابن` path (comma-join several)
- `Images` — comma-joined full IG CDN URLs (first = primary)
- `Active` `1`, `Digital` `0`, `Quantity` e.g. `20`, `Variants` empty
- Quote every cell; escape `"` as `""`.

```js
const fd = new FormData();
fd.append('file', new Blob(['﻿' + csv], { type: 'text/csv' }), 'products.csv');
fd.append('source', 'standard');
fd.append('download_images', '1');
// POST /admin/products/import with the XSRF header + Accept: application/json
```

Then open `/admin/products` and confirm the count and that images appear. If
images are missing (CDN refused the server): upload each one with
`POST /admin/products/images` (`image` file ≤ 2 MB → returns `{path}`) and attach
it by editing the product, or recreate that product via `POST /admin/products`
with `images: [{path, is_primary: true}]`.

## 7. Theme

Official themes: `basic` (default, flexible), `branda`, `khuta`.

| Shop niche | Theme |
|---|---|
| fashion, abayas, dresses, bags, jewelry, perfume/luxury beauty | `branda` — elegant fashion: white page, warm stone, square edges, ink buttons, Ruqaa headings |
| sneakers, streetwear, sport, lifestyle brands with strong photography | `khuta` — bold editorial: linen page, red accent, pill buttons, full-width tiles, huge headings |
| food, sweets, groceries, electronics, general stores, anything else | stay on `basic` |

Switch with `POST /admin/theme/select` `{theme}` (`admin.theme.select`). Non-default
themes need the `install_themes` plan feature (pro/max): if the response says the
plan doesn't allow it, **don't** assign a plan — keep `basic`, write
`notes=+يحتاج باقة لثيم {theme}`, and mention it in the report.

Look at the storefront (`https://{slug}.safqi.app` — while hidden, the logged-in
admin preview `/admin/theme/preview`) and take one screenshot to sanity-check
logo, products and theme.

## 8. Close out

```bash
python3 $SKILL_DIR/scripts/leads.py update "/path/leads.xlsx" ROW \
  status=done store_url=https://{slug}.safqi.app theme={theme} \
  products_count={n} created_at={YYYY-MM-DD} notes="…"
```

Close the Instagram and impersonation tabs. Report to the user in a few lines:
store URL, email + where the password is (the Excel row — don't paste it in chat
unless asked), product count, theme and why, anything estimated or skipped.

On any failure mid-way: write `status=failed notes=<step + error>` (keep the
already-written credentials — the tenant may exist), and tell the user exactly
which step to resume from. A re-run must check for the existing slug and continue
from step 4 instead of creating a duplicate.
