# Quran Recitation Sharing Bot (WhatsApp & Telegram)

Shared Quran recitation for WhatsApp and Telegram groups plus personal recitation plans over DM. Groups split the Quran by **page, surah, hizb, juz (default), or whole Quran** over a configurable cycle (**daily, weekly, monthly, or custom `<N>d`**). Languages: **English**, **Persian (فارسی)**, **Arabic (العربية)**.

## Features

- Configurable recitation unit: `/granularity page|surah|hizb|juz|quran`
- Configurable cycle length: `/cycle daily|weekly|monthly|<N>d` — cycles auto-roll when they expire
- Start a new cycle manually (`/startcycle`, legacy alias `/startweek`)
- Completion reminders on a customizable schedule (`/reminders off|daily|weekly|<N>h|<N>d`, default daily)
- Open-spot announcements on a customizable schedule (`/advertise off|daily|weekly|<N>h|<N>d`, default off)
- Personal recitation plans over DM (`/plan start 1 juz daily`, `/plan status|done|stop`)
- Direct quran.com links to the exact portion in claim confirmations, reminders, and plan messages (e.g. `https://quran.com/juz/5`, `/page/302`, `/hizb/12`, surah `/36`)
- Fully interactive Telegram support with inline buttons and clickable commands for frictionless claiming
- Optional admin نیت (`/niyyah …`)
- Claim / release / mark done portions (`/claim`, `/release`, `/done`)
- Progress (`/status`, `/available`, `/mine`, `/settings`)
- Group language (`/lang en|fa|ar`) with localized command aliases
- Group admins (`/admin`, `/admins`)

## Quick start

```bash
cd quran_bot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# create .env with Meta WhatsApp Cloud API credentials (see Config below)

uvicorn src.main:app --host 0.0.0.0 --port 8080
```

Expose HTTPS (e.g. ngrok) and set the Meta webhook to `https://<host>/webhook` with your verify token.

## Commands

| Action | English | Persian | Arabic |
|---|---|---|---|
| Help | `/help` | `/راهنما` | `/مساعدة` |
| Language | `/lang fa` | `/زبان fa` | `/لغة ar` |
| New cycle | `/startcycle` | `/دوره‌جدید` | `/دورة-جديدة` |
| Recitation unit | `/granularity juz` | `/واحد جزء` | `/وحدة جزء` |
| Cycle length | `/cycle weekly` | `/دوره هفتگی` | `/دورة أسبوعي` |
| Reminders | `/reminders daily` | `/یادآوری روزانه` | `/تذكير يومي` |
| Open-spot ads | `/advertise daily` | `/اعلان روزانه` | `/إعلان يومي` |
| Settings | `/settings` | `/تنظیمات` | `/إعدادات` |
| Intention | `/niyyah …` | `/نیت …` | `/نية …` |
| Available | `/available` | `/آزاد` | `/متاح` |
| Status | `/status` | `/وضعیت` | `/حالة` |
| Claim | `/claim 5` | `/رزرو 5` | `/حجز 5` |
| Release | `/release 5` | `/آزادسازی 5` | `/إلغاء 5` |
| Done | `/done 5` | `/تمام 5` | `/تم 5` |
| Mine | `/mine` | `/من` | `/لي` |
| Personal plan | `/plan start 1 juz daily` | `/برنامه …` | `/خطة …` |

Clear نیت: `/niyyah clear` (or `پاک` / `مسح`).

Granularity and cycle-length changes apply from the **next** cycle, so in-flight claims are never invalidated.

### Personal plans

Anyone can DM the bot a personal khatm plan:

```
/plan start 2 juz daily      # 2 juz per day → khatm in 15 days
/plan start 5 page daily     # 5 pages per day
/plan status                 # progress + current portion
/plan done                   # complete current portion, advance
/plan stop                   # stop the plan
```

The scheduler DMs the day's portion as a check-in on the plan's cycle. Completing a khatm congratulates you and restarts from the beginning.

## Scheduler

Each tick:

1. Auto-rolls expired group cycles and announces the new cycle to members
2. DMs completion reminders to members with unfinished claims (per `/reminders`)
3. Broadcasts open portions to all members (per `/advertise`)
4. Sends personal plan check-ins

Due-ness is stored in the DB (`ends_at`, `last_reminder_at`, `last_ad_at`), so ticks are restart-safe.

### Local / VPS

In-process APScheduler runs when `ENABLE_INLINE_SCHEDULER=true` (default).

### Vercel + cron-job.org

Serverless hosts do not keep APScheduler alive. Use an external cron:

1. Set in Vercel env:
   - `CRON_SECRET` — long random string
   - `ENABLE_INLINE_SCHEDULER=false`
2. On [cron-job.org](https://cron-job.org): create a job every 5 minutes  
   - URL: `https://YOUR-DOMAIN/api/tick` (also works: `/cron/tick`)  
   - Method: GET or POST  
   - Header: `X-Cron-Secret: <same as CRON_SECRET>`  
   - Or append `?secret=<CRON_SECRET>` to the URL
3. A successful run returns JSON like `{"ok": true, "sent": 3, "queued": 3}`.
4. If you still get FastAPI `{"detail":"Not Found"}`, the deployment is stale: in Vercel → Deployments → … on the latest → **Redeploy** and **uncheck “Use existing Build Cache”**.

### WhatsApp template messages (required outside 24h)

Free-form WhatsApp texts only work within **24 hours** of the user’s last message. Scheduled pushes use **approved templates** when configured.

Create Utility templates in Meta Business Suite → WhatsApp → Message templates (one per language you need: `en`, `fa`, `ar`), then set:

| Env | Kind | Suggested body (placeholders) |
|---|---|---|
| `WHATSAPP_TEMPLATE_REMINDER` | reminder | `Reminder — pending: {{1}}. Reply /done when finished.` |
| `WHATSAPP_TEMPLATE_AD` | ad | `Open spots ({{1}} free): {{2}}. Claim with /claim.` |
| `WHATSAPP_TEMPLATE_CYCLE` | cycle_rollover | `New cycle #{{1}} started — {{2}} available. Claim with /claim.` |
| `WHATSAPP_TEMPLATE_PLAN` | plan_checkin | `Your portion: {{1}}. {{2}} — reply /plan done when complete.` |

`{{1}}` / `{{2}}` must match exactly what the bot sends (see table). After Meta approves the templates, put their **names** in env (not the body text).

Send order: template if configured → else free-form text; if free-form hits error `131047` and no template is set, the send is skipped and logged.

## Config (`.env`)

| Var | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `sqlite:///data/quran_bot.db` | Database (Vercel Postgres auto-detected) |
| `WHATSAPP_TOKEN` | — | Meta API token |
| `WHATSAPP_PHONE_NUMBER_ID` | — | Sender phone id |
| `WHATSAPP_VERIFY_TOKEN` | `quran-bot-verify` | Webhook verification |
| `TELEGRAM_TOKEN` | — | Telegram Bot API token |
| `TELEGRAM_SECRET_TOKEN` | — | Optional Telegram webhook secret |
| `BOOTSTRAP_ADMIN_IDS` | — | Comma-separated global super-admin WA ids |
| `DEFAULT_LANGUAGE` | `en` | New group default |
| `SCHEDULER_INTERVAL_SECONDS` | `300` | In-process scheduler tick interval |
| `ENABLE_INLINE_SCHEDULER` | `true` | Set `false` on Vercel |
| `CRON_SECRET` | — | Protects `/cron/tick` for cron-job.org |
| `WHATSAPP_TEMPLATE_REMINDER` | — | Approved template name for reminders |
| `WHATSAPP_TEMPLATE_AD` | — | Approved template name for open-spot ads |
| `WHATSAPP_TEMPLATE_CYCLE` | — | Approved template name for cycle rollover |
| `WHATSAPP_TEMPLATE_PLAN` | — | Approved template name for plan check-ins |
| `WHATSAPP_TEMPLATE_LANG_DEFAULT` | `en` | Fallback Meta template language code |

## Architecture

```
quran_bot/
├── src/
│   ├── main.py              # FastAPI app + APScheduler tick
│   ├── config.py            # Settings from env
│   ├── quran_meta.py        # Granularities + schedule-spec parsing
│   ├── api/                 # Webhook + WhatsApp Cloud client
│   ├── bot/                 # Command parse + handlers
│   ├── services/            # Group cycles / personal plans / scheduler
│   ├── models/              # SQLAlchemy + SQLite
│   └── i18n/                # EN / FA / AR strings
└── tests/
```

State is stored in SQLite by default (`data/quran_bot.db`).

**Upgrading from the juz-only version:** the `weeks` / `juz_claims` tables were replaced by `cycles` / `portion_claims`. New `groups` columns are added automatically on startup; old week/claim data is not migrated — reset the dev database (`rm data/quran_bot.db`) or migrate manually.

## Meta WhatsApp notes

1. Create a Meta app with **WhatsApp** product.
2. Copy **Phone number ID** and a permanent access token into `.env`.
3. Subscribe the webhook to `messages`.
4. For production groups, use a WhatsApp Business number added to the target groups.
5. Set `BOOTSTRAP_ADMIN_IDS` to your WA user id so the first `/help` in a group promotes you to admin (or leave empty to auto-promote the first user who messages when the group has no admins).

## Telegram Setup

1. Create a bot using [@BotFather](https://t.me/botfather) and get the token.
2. Set `TELEGRAM_TOKEN` in `.env`.
3. Set your webhook pointing to `/telegram/webhook` (e.g. `https://api.telegram.org/bot<token>/setWebhook?url=https://<host>/telegram/webhook`).
4. (Optional) set `TELEGRAM_SECRET_TOKEN` for added webhook security.
5. Telegram users will enjoy interactive inline grids for claiming and modifying settings seamlessly without typing commands.

## Tests

```bash
cd quran_bot
python -m pytest tests/ -q
```

## Example cycle flow

1. Admin: `/lang fa`
2. Admin: `/واحد جزء`, `/دوره هفتگی`, `/یادآوری روزانه`, `/اعلان روزانه`
3. Admin: `/دوره‌جدید`
4. Admin: `/نیت شفای بیماران`
5. Members: `/رزرو 1` … `/رزرو 30`
6. Members: `/تمام 1` when finished
7. Anyone: `/وضعیت`
8. The bot auto-starts the next cycle after a week and reminds stragglers daily.
