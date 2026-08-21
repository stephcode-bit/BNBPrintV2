# BNBPRINT — BNB Chain Runner Radar

Real-time BNB Chain token discovery, with a focus on bonding-curve launchpads
(four.meme, GraFun, and similar). BNBPRINT screens every new token for
honeypots, rug pulls, unlocked liquidity, and low security scores, and flags
likely "runners" before their bonding curve finishes — all wrapped in an
installable, offline-capable PWA.

> ⚠️ **This is a working scaffold, not a finished, keys-in-hand product.**
> The whole app runs today with zero credentials in `DEMO_MODE` (a realistic
> simulated token feed). Going live on real BNB Chain data requires you to
> supply an RPC endpoint, optionally an Ave AI key, and — most importantly —
> **verify the bonding-curve factory contract addresses/ABIs yourself**
> (see [Going live](#going-live-turning-off-demo_mode) below). I don't have
> a way to confirm those from this environment, so treat every contract
> address in this repo as a placeholder until you've checked it on BscScan.

> 💰 **This runs for $0/month.** The original design used an always-on
> Railway/Render backend, which costs real money every month once its free
> trial credit runs out. The app was reworked (see
> [§2 Architecture](#2-architecture) and [§5 Deploying](#5-deploying-the-0month-way))
> to replace that always-on process with a scheduled GitHub Actions job +
> Upstash's free Redis tier — no server ever sits there idle burning
> credit. The one honest trade-off: detection latency is "within about
> 30-40 seconds" instead of instant. If you specifically need the old
> instant-WebSocket, always-on architecture and are fine paying ~$5/month
> for it, that code is still in the repo — see the
> [legacy always-on appendix](#appendix-the-old-always-on-architecture-paid).

---

## 1. On your questions (Firebase / database / monthly cost)

**You don't need Firebase, and you don't need Supabase.** BNBPRINT uses:

- **Upstash Redis (free tier — REST API)** as the shared state store
  between the scanner and the frontend. See §2 for why this replaced
  Postgres: it has no monthly compute-hour budget to run out of, which
  matters once the thing reading/writing it runs near-continuously.
- **Standard Web Push (VAPID)** for PWA push notifications — no Firebase
  Cloud Messaging needed. It's a native browser API, works the same on
  Android/desktop, and doesn't add a second cloud vendor or SDK.

Firebase would only earn its place if you later want real user accounts
(Firebase Auth) instead of the current anonymous, per-device identity model.
Bookmarks today are just localStorage on your device (see §2) — if you add
real accounts later, that's the natural point to reach for Firebase Auth
or similar, and swap bookmarks over to synced, server-side storage.

**On the monthly cost question specifically:** the original architecture
(FastAPI backend on Railway, always subscribed to the chain over a
WebSocket, Postgres for storage) is a completely normal, good design — it's
just not free. Any host that keeps a process running 24/7 charges for that,
because you're renting a slice of a server around the clock whether or not
it's doing anything. There's no free tier anywhere that offers true
always-on compute; "free" tiers work by either sleeping the process when
it's idle (which breaks a real-time listener) or by giving you a monthly
compute-hour allowance that a 24/7 process burns through in 2-3 weeks. The
rework in this repo sidesteps that by not running continuously at all —
see §2.

---

## 2. Architecture

```
┌────────────────────────┐              cron (safety-net, every 5h)
│  GitHub Actions          │◀───────────────────────────────────────┐
│  (backend/scan_runner.py) │                                          │
│                            │  each run loops internally for ~5h45m,   │
│  web3.py polling            │  polling every ~15s — so there's        │
│  GoPlus / Ave AI            │  effectively no gap in coverage         │
│  Scoring engine               │  between scheduled restarts             │
└─────────────┬────────────┘                                          │
              │ writes snapshot + stats + push subs                    │
              ▼                                                        │
┌────────────────────────┐                                            │
│  Upstash Redis (free)     │                                            │
│  bnbprint:tokens            │                                            │
│  bnbprint:stats               │                                            │
│  bnbprint:push_subs             │                                            │
└─────────────┬────────────┘                                            │
              │ reads directly (REST API)                                │
              ▼                                                          │
┌────────────────────────┐        polls every ~15-20s        ┌─────────┴──┐
│  Next.js PWA               │◀──────────────────────────────────│  Browser    │
│  (Vercel, incl. app/api/*)  │                                    │  (client)   │
└────────────────────────┘                                    └────────────┘
```

Nothing in this diagram runs 24/7 as a paid always-on process — the
scanner is a *scheduled* job (free, unlimited on a public GitHub repo),
Upstash's free tier has no sleep/cold-start and no compute-hour clock
ticking down, and Vercel's Hobby plan serves the frontend + its API
routes on-demand. Total steady-state cost: $0/month.

- **Scanner**: `backend/scan_runner.py`, triggered by
  `.github/workflows/scanner.yml`. Reuses the same pipeline as before
  (`chain_listener.process_token_pipeline` → GoPlus + Ave AI + on-chain
  checks → `scoring.py`) — only *how* it runs changed, not the security
  logic itself.
- **State store**: `backend/app/services/store.py` (scanner side) and
  `frontend/lib/redis.ts` (frontend side) both talk to the same Upstash
  Redis database over its REST API — a few JSON blobs, not a relational
  schema (see the docstring in `store.py` for the exact key layout).
- **Frontend**: `frontend/` — Next.js 14 (App Router), TypeScript, Tailwind,
  `next-pwa` (custom service worker with Web Push support), React Query. Its
  own `app/api/tokens`, `app/api/stats`, and `app/api/push/*` routes read/
  write Upstash directly — there's no separate backend to deploy or point a
  base URL at.
- **"Live" feed**: `frontend/lib/ws.tsx` keeps the same `useTokenStream()`
  interface a real WebSocket would have had, but internally it's a ~15s
  poll loop that diffs responses and synthesizes the same event types
  (`new_token`, `runner_flagged`, `bonding_complete`) — every component
  that consumes it (Header's LIVE indicator, LiveFeed) is unchanged.
- **Bookmarks**: pure `localStorage`, per device (`frontend/lib/bookmarks.ts`)
  — no server round-trip, since there's no per-user backend anymore.

---

## 3. Repo layout

```
bnbprint/
├── .github/workflows/
│   └── scanner.yml               Schedules backend/scan_runner.py — see §5
│
├── backend/
│   ├── scan_runner.py             $0/month entry point — run by scanner.yml
│   ├── app/
│   │   ├── main.py                 Legacy always-on FastAPI app (see appendix) — unused by default
│   │   ├── config.py                Settings (env vars), incl. DEMO_MODE, Upstash + scan tuning
│   │   ├── database.py, models.py    SQLAlchemy — legacy path only, unused by default
│   │   ├── schemas.py               Pydantic request/response models — legacy path only
│   │   ├── ws_manager.py             WebSocket fan-out — legacy path only
│   │   ├── tasks.py                  Legacy always-on background tasks
│   │   ├── routers/                  Legacy FastAPI routes (tokens, bookmarks, stats, ws, push)
│   │   └── services/
│   │       ├── chain_listener.py      Token pipeline — process_token_pipeline() shared by both paths
│   │       ├── bonding.py              Bonding-curve progress readers (four.meme / GraFun stubs)
│   │       ├── security_checks.py      On-chain honeypot/owner/liquidity-lock checks
│   │       ├── ave_ai.py               Ave AI security API client (cached, best-effort)
│   │       ├── goplus.py                GoPlus honeypot/tax/LP-lock simulator (real, keyless)
│   │       ├── scoring.py               Security score + runner score algorithms
│   │       ├── store.py                 Upstash Redis client — the $0/month state store
│   │       ├── push_runner.py           Web Push sender for scan_runner.py (reads store.py)
│   │       └── push.py                  Web Push sender for the legacy FastAPI path
│   ├── requirements.txt, Dockerfile, railway.json, .env.example
│
├── frontend/
│   ├── app/                     Dashboard, /token/[address], /bookmarks, /about, /offline
│   │   └── api/                  tokens, tokens/[address], stats, push/* — read/write Upstash directly
│   ├── components/               TokenCard, SecurityBadge, BondingProgressBar, CopyButton,
│   │                              BookmarkButton, LiveFeed, FilterBar, StatsBar, TickerTape…
│   ├── lib/                      api.ts, ws.tsx (poll-based), redis.ts, bookmarks.ts (localStorage),
│   │                              userId.ts, push.ts, utils.ts
│   ├── worker/index.js           Custom service worker source (API caching + Web Push)
│   ├── public/                   manifest.json, icons/, favicon.ico
│   └── package.json, next.config.js, tailwind.config.ts, .env.example
│
└── README.md (this file)
```

---

## 4. Local development

### Scanner (the $0/month path)

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# DEMO_MODE=true by default — no credentials needed to see it running.
# Leave UPSTASH_REDIS_REST_URL/TOKEN blank for now — without them, store.py
# no-ops (logs a warning, doesn't crash), which is fine for a quick local
# check. Set them (a free database from upstash.com) to actually see data
# persist and show up in the frontend.
python scan_runner.py
```

By default it loops for 5h45m; for a quick local check, stop it any time
with Ctrl+C, or override the budget: `SCAN_LOOP_BUDGET_SECONDS=30 python
scan_runner.py`. With `DEMO_MODE=true` it starts emitting synthetic tokens
within the first couple of poll cycles, no keys required.

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local   # add the same Upstash credentials as the scanner's .env
npm run dev
```

Visit `http://localhost:3000`. Note: `next-pwa` is disabled in dev mode by
design (Next.js convention) — the service worker, offline support, and
install prompt only activate in a production build (`npm run build && npm start`).

---

## 5. Deploying (the $0/month way)

Four things to set up, all free, no card required anywhere: GitHub (you
already have this), Upstash, GitHub Actions secrets, and Vercel.

1. **Push this repo to GitHub, and make it public.** Public repos get
   unlimited free GitHub Actions minutes, which is what makes the
   near-continuous scanner (§2) free rather than metered. (Nothing secret
   lives in the code — every credential is a GitHub secret or Vercel env
   var, never committed — so making the repo public doesn't expose keys.
   If you'd rather keep it private anyway, it still works: GitHub Free
   gives private repos 2,000 Actions minutes/month, comfortably enough for
   the default 5-hour cron cadence.)
   ```bash
   git remote add origin https://github.com/<you>/bnbprint.git
   git branch -M main
   git add -A && git commit -m "Initial BNBPRINT scaffold"
   git push -u origin main
   ```

2. **Create a free Upstash Redis database.** Go to
   [upstash.com](https://upstash.com) → sign up (no card) → Create Database
   → Redis → pick any region close to you → Create. On the database's
   page, open the **REST API** tab and copy the two values shown there:
   `UPSTASH_REDIS_REST_URL` and `UPSTASH_REDIS_REST_TOKEN`. This one
   database is shared by both the scanner and the frontend — you'll paste
   these same two values into both places below.

3. **Add GitHub Actions secrets/variables** (these feed
   `.github/workflows/scanner.yml`, which runs `backend/scan_runner.py`):
   go to your repo on GitHub → **Settings → Secrets and variables →
   Actions**.
   - Under **Secrets**, add `UPSTASH_REDIS_REST_URL` and
     `UPSTASH_REDIS_REST_TOKEN` from step 2. That's the only secret
     required to get a demo-mode scanner running.
   - Once you're ready to go live (§6), also add `RPC_HTTPS_URL`,
     `GOPLUS_APP_KEY`/`GOPLUS_APP_SECRET`, `AVE_AI_API_KEY`,
     `VAPID_PUBLIC_KEY`/`VAPID_PRIVATE_KEY` as secrets, matching
     `backend/.env.example`.
   - Under the **Variables** tab (same page), you can optionally set
     `DEMO_MODE=false`, `FOUR_MEME_FACTORY`, `GRAFUN_FACTORY`,
     `RUNNER_SCORE_THRESHOLD`, `MIN_SECURITY_SCORE` — these have sane
     defaults baked into the workflow file if you skip them.
   - **Kick off a first run**: go to the **Actions** tab → **BNBPRINT
     Scanner** in the left sidebar → **Run workflow** (this is the
     `workflow_dispatch` trigger — no need to wait for the cron schedule).
     Click into the run and watch the logs; it should start looping and
     writing to Upstash within a few seconds.

4. **Frontend → Vercel.** Import the same GitHub repo into Vercel → set
   **Root Directory** to `frontend`. In **Settings → Environment
   Variables**, add the *same* `UPSTASH_REDIS_REST_URL` /
   `UPSTASH_REDIS_REST_TOKEN` from step 2 (and `VAPID_PUBLIC_KEY` /
   `VAPID_PRIVATE_KEY` if you're using push). Deploy — Vercel auto-detects
   Next.js and runs `next build`. That's it: no CORS to configure (the API
   routes are same-origin), no backend domain to generate, no second
   service to keep alive.

Once both are live, open your Vercel URL — you should see tokens appearing
within the first scanner cycle (or immediately if the Actions run from
step 3 already populated Upstash before you deployed the frontend).

## 6. Going live: turning off `DEMO_MODE`

Flip `DEMO_MODE=false` only after you've done the following — the app is
built to be honest about risk, and shipping fabricated bonding-curve
progress or security data to real users would defeat the entire point:

### 6.1 RPC keys (an API — sign up, get a URL)

Pick one: [QuickNode](https://www.quicknode.com/chains/bnb),
[Alchemy](https://www.alchemy.com/bnb-smart-chain), or
[Ankr](https://www.ankr.com/rpc/bsc/). Free tiers exist on all three.

1. Sign up, create an endpoint for **BNB Smart Chain — Mainnet**.
2. Copy both the **HTTPS** and **WebSocket (WSS)** URLs it gives you.
3. Set `RPC_HTTPS_URL` and `RPC_WSS_URL` in `backend/.env`.

That's the whole step — no ABI involved here, this is purely a connection
to the chain.

### 6.2 Verified factory ABIs (this is an ABI, not an API)

To answer your question directly: an **ABI** (Application Binary Interface)
is a JSON description of a specific contract's functions/events — it's not
a web service you call, it's a schema that belongs to one exact contract
address, and `web3.py` needs it to decode logs or call read functions like
`getCurveProgress()`. There's no "four.meme API" to hit for this — the
source of truth is the verified contract itself.

How to get it, step by step:

1. **Find the real factory/bonding-curve-manager address.** Don't trust
   any address you find secondhand (including the placeholders in this
   repo, and including the ones you pasted earlier — I still haven't been
   able to verify those from this sandbox). The reliable way: find a token
   you *know* launched on four.meme (or GraFun), open its contract on
   [BscScan](https://bscscan.com), go to its creation transaction, and look
   at "Interacted With (To)" — that's the factory/manager contract that
   deployed it.
2. **Open that address on BscScan.** If it's verified, there's a
   **Contract** tab with a **Code** sub-tab showing the ABI as JSON, with a
   copy button right there in the UI.
3. **Or fetch it programmatically via BscScan's API** (free, separate key
   from your RPC key — get one at
   [bscscan.com/myapikey](https://bscscan.com/myapikey)):
   ```
   https://api.bscscan.com/api?module=contract&action=getabi&address=0xTHE_FACTORY&apikey=YOUR_BSCSCAN_KEY
   ```
   The response's `result` field is the ABI JSON, ready to paste in.
4. **Paste it into the code.** Open `backend/app/services/bonding.py` and
   set `FourMemeReader.CURVE_ABI` (or `GraFunReader.CURVE_ABI`) to that
   JSON array, then fill in the commented-out example call in `.read()`
   with the actual function names from the ABI (they won't be exactly
   `raisedBNB`/`targetBNB` — those were illustrative). Put the confirmed
   address in `FOUR_MEME_FACTORY` / `GRAFUN_FACTORY` in `backend/.env`.
5. If the contract **isn't verified** on BscScan, there's no ABI to copy —
   check the platform's official GitHub/docs for their published ABI
   instead. Never reverse-engineer one from raw bytecode as a first resort.

### 6.3 A real honeypot simulator — **done, this one's already wired in**

I implemented this one directly rather than leaving it as a stub:
`backend/app/services/goplus.py` calls the
[GoPlus Security API](https://docs.gopluslabs.io/reference/token-security-api)
— a free, purpose-built third-party API (not an ABI — this one really is a
web service) that runs the buy/sell simulation server-side and returns
honeypot risk, buy/sell tax, LP-lock status, mintability, and holder
concentration as plain JSON. It's now the primary signal for all of that in
`chain_listener.process_token_pipeline`, with Ave AI and our own on-chain
checks as fallbacks whenever GoPlus doesn't have an opinion.

- **No key required** to start — it works out of the box at a public rate
  limit once `DEMO_MODE=false`.
- **Optional, for higher volume:** sign up free at
  [gopluslabs.io](https://gopluslabs.io/) for an App Key + Secret, set
  `GOPLUS_APP_KEY` / `GOPLUS_APP_SECRET` in `backend/.env`.
- I couldn't hit the live GoPlus API from this sandbox to test a real
  response (same network restriction that blocked BscScan/Google
  Fonts here) — the error handling is defensive (falls back to Ave AI /
  on-chain, same pattern as everywhere else in this codebase) and the code
  path was verified to run without crashing, but confirm the first few
  real responses look sane once it's deployed somewhere with normal
  internet access.
- If you want the deeper, fully-custom version instead (simulating the
  exact router/curve contract yourself via a state-override `eth_call`),
  `security_checks.simulate_buy_sell()` is still there as the place to
  build that — GoPlus covers the same need with far less work, so I'd only
  reach for that if GoPlus ever misses a case specific to a launchpad's
  bonding-curve buy/sell path (which uses the curve contract directly
  rather than a standard DEX router, and GoPlus may not model that).

### 6.4 Optional extras

- **Ave AI key** — `AVE_AI_API_KEY` as a GitHub Actions secret (§5 step 3).
  Works without it (falls back to GoPlus + on-chain), adds a second
  independent signal.
- **Web Push** — generate a VAPID keypair (see the comment atop
  `backend/app/services/push_runner.py`) and set `VAPID_PUBLIC_KEY` /
  `VAPID_PRIVATE_KEY` as **both** a GitHub Actions secret (the scanner
  sends the push) **and** a Vercel environment variable (the frontend
  serves the public key to the browser and accepts subscriptions) — same
  keypair in both places.

---

## 7. Known limitations / next steps

- **Detection latency is ~30-40s, not instant.** This is the direct
  trade-off of the $0/month rework (§2) — see the note at the top of this
  README. If that's ever not fast enough, the always-on architecture in
  the [appendix](#appendix-the-old-always-on-architecture-paid) gets you
  back to instant WebSocket push, for ~$5/month.
- **GitHub Actions' schedule trigger isn't a hard real-time guarantee.**
  GitHub's own docs note scheduled workflows "may be delayed during
  periods of high load" on their infrastructure. The 5-hour cron cadence
  against each run's ~5h45m internal budget leaves a comfortable margin
  (a scheduling delay would need to exceed ~45 minutes to actually create
  a coverage gap), but it's not a contractual SLA the way a paid always-on
  host's uptime is — worth knowing rather than assuming "scheduled every
  5h" means "exactly every 5h, always."
- **Live-mode token *detection* still needs each bonding platform's
  verified ABI to fully decode** (`backend/scan_runner.py`'s `_live_tick()`
  and `backend/app/services/bonding.py`'s `CURVE_ABI` TODOs) — this was
  already true before the $0/month rework and is unchanged by it; see §6.2.
- **No historical price/volume charts yet.** The token detail page renders
  a live *session* sparkline (accumulated while the page is open) rather
  than true historical OHLC data. `store.py`'s snapshot could be extended
  with a capped per-token price-tick list (Redis list + `LTRIM`) if you
  want real charts without bringing back a relational database.
- **Holder-growth-rate and bonding-speed inputs to the runner score are
  randomized in DEMO_MODE** and are TODO'd for live mode — computing them
  for real means tracking snapshots over time per token (same extension
  as the point above).
- **Contract verification status** (`contract_verified`) now comes from
  GoPlus (`is_open_source`) or Ave AI, whichever responds; add a direct
  BscScan `getsourcecode` API call if you want a third independent source.
- No automated test suite yet — `backend/scan_runner.py` was smoke-tested
  end-to-end in DEMO_MODE (see §4) and `frontend` was type-checked and
  production-built successfully, but there's no CI.

---

## 8. Brand

"BNBPRINT" uses the BNB Chain / Binance color language: `#F0B90B` (BNB
yellow) as the single accent color, `#0B0E11` / `#181A20` / `#1E2329` dark
surfaces, `#0ECB81` green / `#F6465D` red for buy/sell-style signals. See
`frontend/tailwind.config.ts` (`theme.extend.colors.bnb`) — every component
pulls from that token set rather than hardcoded hex values.

---

## Appendix: the old always-on architecture (paid)

The always-on FastAPI + Postgres design this project started with is still
in the repo, untouched and working — `backend/app/main.py`,
`app/database.py`, `app/models.py`, `app/tasks.py`, `app/routers/*`, and
`app/services/push.py`. It's just not what gets deployed by default
anymore (§5). Reasons you might still want it: genuinely instant
(sub-second) WebSocket push instead of ~30-40s polling, or you'd rather
have a real relational database for future features (historical charts,
per-user accounts) than grow those on top of a Redis snapshot.

To use it instead of the $0/month path:

1. **Backend → Railway (or Render).**
   - [railway.app](https://railway.app) → New Project → Deploy from GitHub
     repo → pick `bnbprint`.
   - Railway will try to build the repo root — open the new service's
     **Settings** tab and set **Root Directory** to `backend`, since this
     is a monorepo. It'll then pick up `backend/Dockerfile` automatically.
   - Add a database: in the project, click **+ New → Database → Add
     PostgreSQL**. Then in your backend service's **Variables** tab, add a
     reference variable pointing `DATABASE_URL` at the Postgres plugin's
     connection string (Railway lists it for you to link, rather than you
     typing it by hand).
   - Add the rest of the variables from `backend/.env.example` in the same
     **Variables** tab (at minimum, leave `DEMO_MODE=true` for now).
   - **Get the public URL** — Railway services aren't exposed to the
     internet by default. Go to **Settings → Networking → Generate
     Domain**. That gives you something like
     `bnbprint-backend-production.up.railway.app`.
   - Sanity-check it: open `https://<that-domain>/health` in a browser —
     you should see `{"status": "healthy"}`. If not, check the service's
     **Deployments → Logs** tab for the error before moving on.

2. **Frontend → Vercel**, pointed at the backend instead of Upstash:
   - `NEXT_PUBLIC_API_URL` = `https://` + the Railway domain
   - `NEXT_PUBLIC_WS_URL` = `wss://` + the Railway domain + `/ws/tokens`
   - You'll also need to restore `frontend/lib/api.ts` and
     `frontend/lib/ws.tsx` to fetch that base URL / open a real WebSocket
     instead of calling the local `app/api/*` routes — the current
     versions are written for the Upstash-direct path. Git history has the
     pre-rework versions if you want a reference.
   - Import the repo into Vercel → **Root Directory** = `frontend` → add
     both env vars → deploy.

3. **Close the loop: CORS.** Railway → your backend service → Variables →
   set `CORS_ORIGINS` to your Vercel domain (e.g.
   `https://bnbprint.vercel.app`).

**If Railway keeps showing "Deployment failed":** the build finishing but
the deploy still failing almost always means the container built fine but
never became reachable.

1. **Port mismatch (the most common cause, and already fixed in this
   repo).** Railway assigns a random `$PORT` at runtime and health-checks
   whatever port your container is *actually* listening on — a Dockerfile
   that hardcodes `--port 8000` will build successfully and then fail
   every health check. `backend/Dockerfile` reads `${PORT:-8000}` at
   container start already; `backend/railway.json` also explicitly points
   Railway at the Dockerfile builder and a `/health` health-check path.
2. **Root Directory isn't set to `backend`.** If Railway is building from
   the repo root, it may fail to find `Dockerfile`/`requirements.txt`
   entirely (this shows up as a Railpack "could not determine how to
   build the app" error, not a Docker error) — Service → Settings → Root
   Directory must read `backend`, not blank.
3. **Read the actual failure, not just "Failed."** Click into the failed
   deployment → separate **Build Logs** and **Deploy Logs** tabs. Build
   Logs show `pip install`/Docker errors; Deploy Logs show the container's
   own stdout/stderr — the real error is almost always in one of those
   two, even when the top-level status just says "Failed."
