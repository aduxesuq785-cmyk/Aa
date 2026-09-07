# SOHAG BD SHOP — Premium Digital Services

A mobile-first digital goods shop front-end: **VPN, OTT platforms, proxies,
Telegram bots, tools, license keys, AI subscriptions** with a wallet
(deposit + fund-transfer) and an auto-delivery order system.

This repository is a **self-contained static build**: the pages normally
talk to a PHP backend + a Telegram bot, and because that backend is not
part of this repo, a small **demo backend layer** (in `app-boot.js`)
answers the `api_*.php` calls locally from the browser. That makes the
whole flow clickable on any static host — including GitHub Pages — with
**no server required**.

## Pages

| File | What it does |
|---|---|
| `index.html` | Home / category showcase |
| `shop.html` | Category plans (auto-generated demo catalogue) |
| `login.html` | Two-step Telegram-ID + OTP login |
| `account.html` | Profile, status & wallet |
| `deposit.html` | Deposit via bKash / Nagad / Rocket / Binance / BEP20 |
| `deposite.html` | Redirect → `deposit.html` (legacy typo) |
| `pending.html` | Deposit history (auto-approved a few seconds after submit in demo) |
| `orders.html` | Orders (auto-"delivered" with sample keys in demo) |

## Run it

Any static server works — no install, no build:

```bash
# Python
python3 -m http.server 8080
# or Node
npx serve .
```

Open `http://localhost:8080` → *Login*.

### Demo login (important)

There is no real Telegram bot in this demo, so:

1. On **Login**, type any Telegram-style numeric ID (5+ digits), e.g. `123456789`.
2. Tap **Send Code** — because the demo backend is active, the one-time
   code is displayed on screen inside the login card.
3. Type it → you are logged in.

### Demo behaviours

- **Deposits** are recorded as *Pending* and auto-*Approved* after ~12 s
  (balance credited). Try a small bKash deposit on `deposit.html`.
- **Orders** placed in `shop.html` start *Pending* and are auto-*Completed*
  after ~9 s with sample `BRDX-…` keys in `orders.html`.
- **Fund Transfer** (inside `deposit.html`) can be tried against the seeded
  recipients `123456789` or `8801618202470`.
- **Balance** lives in the browser's `localStorage` under the `sbd:` prefix.

## Using the real PHP backend

The repository intentionally ships no backend files. When you host the real
backend (PHP + `api_user_login.php`, `api_balance.php`, … and the Telegram
bot), the demo layer must be turned off so requests reach your server:

- Open the site with `?demo=0`, **or**
- In `app-boot.js` set `var DEMO = false;` (top of the file).

The demo endpoints return the same JSON contracts as the PHP originals, so
no page edits are needed either way.

## GitHub Pages

To publish at `https://<username>.github.io/<repo>/`:

1. Repo → **Settings** → **Pages**
2. Source: **Deploy from a branch** → branch `main`, folder `/ (root)`
3. Save — the site is live at the URL above.

All asset links are relative, so the site also works under a sub-path.

## Assets & credits

- Icons/fonts: Font Awesome Free 6.5.2 (icons `CC BY 4.0`, fonts `SIL OFL`).
  The relevant woff2 files and the generated subset stylesheet live in the
  repo root.
- Category art & payment tiles in this build are generated placeholders —
  replace `*.jpg/png` next to the pages with your own brand images.
- `requirements.txt` (flask / requests / firebase-admin) refers to the
  original server-side deployment and is unused by this static build.
