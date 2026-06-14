# Developer Handbook for AI Agents

## Introduction

This repository is a Django-based Telegram bot called **Petrovich**. It is not a small demo app and not a generic starter template: it is a long-lived, feature-rich bot with production-coupled behavior, multiple external integrations, persistent bot state, and a lot of user-facing functionality implemented as commands.

If you are a new AI agent working in this codebase, optimize for **safe navigation first, small changes second, speed third**.

At a high level, the system works like this:

1. Django exposes webhook endpoints for Telegram and GitHub; Telegram can also be consumed by a local long-polling management command for debug.
2. Incoming Telegram updates are converted into an internal `Event` object.
3. The bot routes that event to a command from the command registry.
4. Commands build one or more `ResponseMessageItem` objects.
5. `TgBot` sends those responses back through the Telegram Bot API.

This project is heavily centered on:

- Telegram chat interactions
- a command-based architecture
- GPT integrations
- media downloading / reposting
- reminders and scheduled tasks
- meme storage / inline search
- GitHub issue/comment automation
- some host-specific operational automation such as Minecraft service control

The code and user-facing strings are predominantly **Russian**, and several operational assumptions are clearly tailored to the maintainer's own infrastructure.

## What this handbook is for

This file is written for **AI agents** that need to:

- understand the repo quickly
- find the right place to make changes
- avoid breaking production-coupled behavior
- choose safe validation steps
- avoid “cleanup” edits that would silently change infrastructure assumptions

Use this document as the first orientation pass before editing code.

---

## Project identity and purpose

- **Project name:** `petrovich`
- **Type:** Django application / Telegram bot
- **Primary interface:** Telegram webhook bot
- **Secondary interface:** GitHub webhook receiver
- **Repository:** `https://github.com/Xoma163/petrovich`
- **README signal:** the bot is linked publicly from the README and an external wiki is referenced there

Based on the codebase, this is a **personal/community utility bot** rather than a generic product platform. It contains broad feature coverage in one repo, including:

- conversational GPT commands
- voice recognition
- social-media/media downloading
- reminders and scheduled commands
- meme and inline meme flows
- games
- issue reporting into GitHub
- admin/moderation utilities
- Minecraft server control

## Tech stack

- **Language:** Python `>=3.14`
- **Framework:** Django `>=6.0.3`
- **Database:** PostgreSQL
- **Cache / ephemeral state:** Redis via `django-redis`
- **Deployment shape:** gunicorn + nginx + systemd-oriented Linux deployment; local debug can use Docker Compose for PostgreSQL and Redis
- **Dependency manager in active use:** `uv` appears current (`uv.lock`, `uv sync` in production update script)
- **Notable libraries/integrations:**
  - Telegram Bot API integration
  - `yt-dlp`
  - `yandex-music`
  - `selenium`
  - `pydub`
  - `pillow`
  - `sentry-sdk`
  - `python-json-logger`
  - OpenAI-compatible GPT provider implementations

## Runtime assumptions

The application expects all of the following to exist:

- PostgreSQL
- Redis
- `.env`
- Telegram bot credentials
- Sentry DSN
- GitHub token for issue automation
- ImgBB key for image upload in GitHub issue/comment flows
- Fernet secret for encrypted stored GPT keys

`ALLOWED_HOSTS` is configurable through `.env` as a comma-separated list. The application always appends `127.0.0.1` and `localhost` so Telegram webhooks and same-host dashboards can call `http://127.0.0.1:10010/...` without depending on the public domain.

Gunicorn also reads `.env` directly and takes its bind settings from `GUNICORN_BIND_ADDRESS`
and `GUNICORN_BIND_PORT` (defaults: `127.0.0.1` and `10010`).

Important: the code strongly suggests a **local Telegram Bot API server mode** and some **hardcoded LAN IP** assumptions.

Current hardcoded operational endpoints discovered in code:

- local Telegram Bot API server: `192.168.1.10:11060`
- Django debug/app port assumption: `10010`
- Qwen/llama.cpp-compatible servers. `QWEN_API_BASE_URLS`

---

## Top-level repository map

### Root

- `manage.py` — Django CLI entrypoint; `runserver` also clears some cached action keys
- `pyproject.toml` — project metadata and Python dependencies
- `uv.lock` — locked dependency graph
- `README.md` — very short overview and external wiki pointer
- `DEVELOPER.md` — this handbook
- `update_production.sh` — production update script
- `pg_backup.sh` — PostgreSQL backup helper
- `docker-compose.local.yml` — loopback-only local PostgreSQL/Redis services for debugging

### Application code

- `apps/bot/` — bot platform models, webhook views, event/message abstractions, Telegram bot implementation
- `apps/commands/` — the actual feature set exposed as commands
- `apps/connectors/` — external APIs and parsers
- `apps/shared/` — shared models, exceptions, utils, mixins, management commands
- `petrovich/` — Django project package (`settings.py`, `urls.py`, `wsgi.py`, etc.)

### Infra / operational

- `config/setup/` — machine/bootstrap setup script
- `config/gunicorn/` — gunicorn configuration
- `.github/workflows/` — CI/deploy workflow definitions
- `secrets/` — committed example env file; real env expected outside git

### Runtime / generated directories

- `media/` — uploaded/generated media
- `staticfiles/` — static assets checked into repo
- `logs/` — app logs
- `templates/` — Django template directory

---

## Read these files first

If you need to understand the system quickly, read in this order:

1. `petrovich/settings.py`
2. `petrovich/urls.py`
3. `apps/bot/views.py`
4. `apps/bot/core/bot/bot.py`
5. `apps/bot/core/bot/telegram/tg_bot.py`
6. `apps/bot/core/event/event.py`
7. `apps/bot/core/event/telegram/tg_event.py`
8. `apps/commands/command.py`
9. `apps/commands/registry.py`
10. then the specific feature area you are changing

For feature-heavy areas:

- GPT: `apps/commands/gpt/`
- Media: `apps/commands/media_command/`
- Reminders: `apps/commands/notifies/`
- Memes: `apps/commands/meme/`
- Utility / image-generation commands: `apps/commands/other/`, shared helpers in `apps/shared/utils/`
- GitHub automation: `apps/commands/other/commands/issue.py`, `apps/commands/other/commands/service/github_reply.py`, `apps/bot/views.py`

---

## Request flow and architecture

## 1. HTTP ingress

Only a very small set of routes is exposed:

- `/admin/`
- `/healthcheck`
- `/bot/tg-webhook`
- `/bot/github`

Relevant files:

- `petrovich/urls.py`
- `apps/bot/urls.py`
- `apps/bot/views.py`

### Telegram ingress

`TelegramView`:

- validates the Telegram webhook secret header if configured
- parses request JSON
- creates `TgBot()`
- hands the raw update to `TgBot.parse()`

`TgBot.parse()` then starts a new thread and calls `handle_event()`.
That worker explicitly closes Django DB connections before reuse and again when the thread exits; if you add more ad-hoc bot threads that touch ORM state, preserve the same cleanup pattern or PostgreSQL connection slots can be exhausted.

For local debugging without exposing a webhook, `python manage.py poll_tg` runs Telegram `getUpdates` polling through the same `TgBot.parse()` path. Use `--drop-webhook` when Telegram still has a webhook configured; add `--drop-pending-updates` only when old queued updates should be discarded.

### GitHub ingress

`GithubView` handles issue/comment/label lifecycle webhooks and sends Telegram notifications back to users. This means GitHub automation is not isolated to a connector layer; webhook behavior directly affects user messaging.

## 2. Internal event model

Telegram updates are normalized into `TgEvent`, which extends the generic `Event` abstraction.

Key responsibilities of `TgEvent`:

- detect update type
- normalize message text
- determine sender/chat context
- parse callback payloads
- parse attachments
- parse reply/forward context
- attach topic/thread metadata
- decide whether the bot should respond

Important behavior:

- reply/forward chains matter
- callback button payloads matter
- inline mode exists
- forwarded messages from chats are often intentionally ignored
- message data is cached into Redis for later reply-chain reconstruction

## 3. Routing

`Bot.handle_event()` is the central high-level execution pipeline:

- `event.setup_event()`
- `event.need_a_response()`
- `bot.route(event)`
- exception handling and user-friendly error responses
- structured logging
- response sending

`Bot.route()` uses the command registry from `apps/commands/registry.py`.

There are two routing modes:

- **normal commands** via `registry_commands`
- **implicit/extra acceptance** via `registry_accept_extra_commands`

That second path is important: some commands react even when the user did not explicitly type the command name.

Examples:

- media links can trigger media processing automatically
- voice recognition/media features may react to attachments or message shape

## 4. Command abstraction

All user-facing features are implemented as command classes derived from `Command` or `AcceptExtraCommand`.

The base class handles:

- command name matching
- role/access enforcement
- PM vs chat restrictions
- forwarded-message requirements
- argument validation
- integer arg parsing
- attachment requirements
- mention/no-mention logic
- help-button creation

This means command behavior is defined not only by `start()`, but also by class attributes such as:

- `name`
- `names`
- `priority`
- `access`
- `pm`
- `conversation`
- `args`
- `attachments`
- `mentioned`
- `non_mentioned`

When changing any command, inspect both:

- its `accept()` logic
- its `start()` logic
- its declarative guardrails in class attributes

## 5. Response model

Commands usually return `ResponseMessage` containing one or more `ResponseMessageItem` objects.

`TgBot` is responsible for:

- choosing Telegram API methods
- formatting text and markup
- chunking long messages
- handling media groups
- editing messages
- retrying around some Telegram API errors
- deleting original messages in some flows

If your change touches output behavior, you may need to trace through:

- `apps/bot/core/messages/`
- `apps/bot/core/bot/telegram/tg_bot.py`

---

## Main subsystems

## Bot/platform core: `apps/bot/`

This is the framework layer of the app.

Important areas:

- `views.py` — webhook entrypoints
- `models.py` — users, chats, roles, profile settings, chat settings
- `core/bot/` — generic and Telegram bot implementations
- `core/event/` — normalized event model
- `core/messages/` — messages, attachments, formatting, parse modes
- `tests/` — currently minimal message parsing tests

Core domain entities in `apps/bot/models.py`:

- `Profile` — main person identity and roles
- `User` — platform-specific user identity (e.g. Telegram account)
- `Chat` — chat/conversation record
- `Role` — permission model
- `ProfileSettings` / `ChatSettings` — bot behavior toggles

## Commands: `apps/commands/`

This is the feature layer.

Feature groups:

- `games/` — Petrovich game and Wordle
- `gpt/` — ChatGPT/Grok/Qwen integrations, models, presets, keys, stats, preprompts
- `media_command/` — URL-driven media extraction/download/caching/reposting
- `meme/` — meme storage, approval, inline meme search
- `notifies/` — reminders and delayed command execution
- `other/` — utility, moderation, profile, settings, issue filing, Minecraft, stats, etc.

`apps/commands/registry.py` is the authoritative command list.

If you add a command but forget the registry, it will not run.

## GPT subsystem: `apps/commands/gpt/`

This is one of the most complex parts of the repo.

What it does:

- text completions
- vision flows
- image generation
- voice recognition
- provider-specific key storage
- per-user provider settings
- per-user presets/preprompts
- usage and cost accounting
- optional streaming behavior
- Telegram Bot API 10.1 rich-message output for GPT text/vision replies
- reply-chain conversation continuation

Important concepts:

- provider models are stored in the database
- user API keys are encrypted with Fernet
- GPT conversation history is reconstructed from cached Telegram messages in Redis
- some GPT provider implementations are OpenAI-compatible, but not all are remote SaaS-only
- Qwen/llama.cpp server discovery uses `QWEN_API_BASE_URLS`, a comma-separated list of base URLs;
  local debugging can point it at a locally reachable tunnel/proxy while production can keep LAN hosts

Providers discovered in code:

- OpenAI / ChatGPT
- xAI / Grok
- local-network Qwen-compatible server

High-risk files:

- `apps/commands/gpt/commands_utils/gpt/gpt_abstract.py`
- `apps/commands/gpt/models.py`
- provider API files in `apps/commands/gpt/api/providers/`

GPT text and vision responses are prepared as both Telegram MarkdownV2 text and Bot API 10.1
`InputRichMessage` markdown. `TgBot.send_message()` and `send_message_draft()` prefer
`sendRichMessage` / `sendRichMessageDraft` when `ResponseMessageItem.rich_markdown` is set. This assumes
the local Telegram Bot API server supports Bot API 10.1 or newer.

## Media subsystem: `apps/commands/media_command/`

This is another large, integration-heavy area.

What it does:

- detects media URLs in user messages
- normalizes accepted Instagram media URLs inside the Instagram service, converting `/reel/` to `/reels/` and removing tracking query/fragment data
- extracts Instagram media from both older `xdt_api__v1__...` page JSON and newer `xig_polaris_media` page JSON
- chooses a service implementation by hostname
- downloads or extracts content
- may cache downloaded videos
- may convert video to audio
- may persist content to disk for admins
- reposts content back into Telegram
- may delete the original user message after successful repost

Reddit media captions can contain Markdown links generated by the service; the media command now sends
those captions through `ResponseMessageItem.rich_markdown` / Telegram rich messages rather than
Telegram MarkdownV2. Other media captions still use HTML parse mode.

The trusted `/аудио` (`/аудиодорожка`) command extracts an AAC audio track from an uploaded
Telegram video. When the command is called as a reply to a video, the returned audio upload uses
the replied video's caption as the sanitized file name; videos without a usable caption still fall
back to `audiotrack.aac`.

Supported service families discovered in code include:

- YouTube video
- YouTube Music
- VK Video
- TikTok
- Reddit
- Instagram
- Twitter / X
- Yandex Music
- Pinterest
- Coub
- Twitch Clips
- Suno AI
- Boosty

Important files:

- `apps/commands/media_command/commands/media_command.py`
- `apps/commands/media_command/service.py`
- `apps/commands/media_command/services/`
- `apps/commands/media_command/models.py`

Shared Selenium browser sessions from `apps/connectors/parsers/web_driver.py` force English locale through Chrome DevTools Protocol (`Accept-Language: en-US,en;q=0.9` and `Emulation.setLocaleOverride`) so parser-visible site text is less dependent on the host OS locale.

## Reminder/scheduler subsystem: `apps/commands/notifies/`

This subsystem stores reminders in the database and dispatches them via management command.
The implementation is split between the user-facing command, shared reminder services, and the background runner.

Behavior includes:

- one-time reminders
- crontab-like reminders
- optional sender mentions
- re-sending saved Telegram attachments via stored file IDs
- delayed execution of bot commands by synthesizing an `Event`

Key files:

- `apps/commands/notifies/models.py`
- `apps/commands/notifies/services.py`
- `apps/commands/notifies/management/commands/check_notify.py`
- `apps/commands/notifies/commands/notifies.py`

## Meme subsystem: `apps/commands/meme/`

This subsystem stores reusable meme assets and powers inline meme search.

Key data concepts:

- approval flag
- trusted-only flag
- TG file ID reuse
- usage counters
- preview assets
- media content preservation

When approved video memes are saved to disk, `_save_meme()` also stores `file_preview`.
YouTube links prefer the public YouTube thumbnail; ordinary uploaded videos and fallback cases
derive a JPEG preview from the already-downloaded video bytes through `VideoHandler.get_preview()`,
which currently takes a frame from the first second by default.

## GitHub automation

GitHub is used both as an external integration and as part of the user support flow.

Capabilities discovered:

- create GitHub issues from bot command `/баг`
- upload attached images to ImgBB and embed them in GitHub issue/comment bodies
- notify developer in Telegram when an issue is created
- notify users in Telegram when issue state/comments/labels change
- allow users to reply to developer comments through Telegram

Key files:

- `apps/connectors/api/github/github.py`
- `apps/commands/other/commands/issue.py`
- `apps/commands/other/commands/service/github_reply.py`
- `apps/bot/views.py`

## Operational / server-control code

Some code performs machine-level or host-level actions.

Example:

- Minecraft server control uses `sudo systemctl start/stop ...`

Treat this area as operationally sensitive.

---

## Important data model summary

Useful mental model:

- `Profile` = person + roles + settings
- `User` = platform account bound to a profile
- `Chat` = Telegram conversation record
- `Notify` = scheduled reminder or delayed command
- `Meme` / `HoroscopeMeme` = stored reusable content
- `VideoCache` = cached downloadable media
- GPT models/settings/presets/preprompts/usages = database-configured AI subsystem state
- `Service` = generic shared key/value storage table

---

## Environment and configuration

## Main settings file

`petrovich/settings.py` is the primary source of truth.

Important characteristics:

- reads env from `.env`
- hard-fails on several required settings
- contains domain/IP assumptions
- configures installed apps, DB, cache, logging, and Sentry
- assumes PostgreSQL and Redis

## Important environment variables discovered

From the codebase and example env:

- `SECRET_KEY`
- `DEBUG`
- `DATABASE_URL`
- `REDIS_URL`
- `SENTRY_URL`
- `FERNET_SECRET_KEY`
- `TG_WEBHOOK_SECRET`
- `TG_BOT_TOKEN`
- `TG_BOT_LOGIN`
- `TG_BOT_GROUP_ID`
- `TG_MODERATOR_CHAT_PK`
- `TG_PHOTO_UPLOADING_CHAT_PK`
- `QWEN_API_BASE_URLS`
- `DISK_SAVE_PATH`
- `IMGBB_API_KEY`
- `GITHUB_TOKEN`

## Secrets handling guidance

- Do not print secrets into logs or docs.
- Do not commit real env files.
- GPT provider keys are encrypted using `FERNET_SECRET_KEY`; changes in this area can invalidate stored keys if mishandled.

---

## Local setup and useful commands

These commands were discovered from project files. They are documented here because they are present in the repo, not because they were executed during this scan.

## Recommended local bootstrap

The repository currently suggests `uv` as the most current dependency workflow.

### 0. Install prerequisites

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
sudo apt install -y libpq-dev gcc python3-dev redis ffmpeg chromium chromium-driver
```

### 1. Install dependencies

```bash
uv sync
```

If you need the local developer toolchain as well, install the dev dependency group:

```bash
uv sync --group dev
pre-commit install
```

### 2. Prepare environment

Create `.env` based on `.env.example`, then provide real values.
The checked-in local example points PostgreSQL and Redis at `127.0.0.1:15433` and `127.0.0.1:16380`, matching `docker-compose.local.yml`; it also keeps the local Telegram Bot API server at `192.168.1.10:11060`.

For local debug dependencies only:

```bash
docker compose -f docker-compose.local.yml up -d
```

### 3. Run migrations

```bash
python manage.py migrate
```

### 4. Initialize seed data

```bash
python manage.py initial
```

This seeds at least:

- roles
- offline city/timezone data

### 5. Run the app locally

```bash
python manage.py runserver
```

Note: `manage.py` runs a one-time cache cleanup when `runserver` starts.

## Useful management commands

Discovered management commands include:

```bash
python manage.py initial
python manage.py crontab_handler
python manage.py check_birthday
python manage.py auto_delete
python manage.py check_pasha_news
python manage.py download_memes
python manage.py reset_migrations
python manage.py check_notify
python manage.py poll_tg --drop-webhook
```

`poll_tg` is intended for local debugging; it keeps webhook behavior untouched unless `--drop-webhook` is provided.

## Tests

Minimal test coverage is currently present.

The repo contains at least:

```bash
python manage.py test
```

There is a small committed test file focused on message parsing:

- `apps/bot/tests/test_message.py`

## Developer tooling

The repository also includes a small local quality toolchain for development:

- `ruff` for linting
- `mypy` for type checking
- `add-trailing-comma` for normalizing trailing commas
- `pre-commit` to run these tools on staged Python files

Quality-tooling note:

- Django `migrations/` directories are excluded from formatter/linter flows (`ruff`, `mypy`, pre-commit hooks)

Typical commands:

```bash
uv run ruff check .
uv run mypy .
uv run pre-commit run --all-files
```

## Static collection

```bash
python manage.py collectstatic --noinput
```

## Production update flow

`update_production.sh` currently does:

```bash
GUNICORN_BIND_PORT_VALUE="$(grep -E '^GUNICORN_BIND_PORT=' .env | tail -n 1 | cut -d '=' -f 2- | tr -d '"' || true)"
DEFAULT_HEALTHCHECK_URL="http://127.0.0.1:${GUNICORN_BIND_PORT_VALUE:-10010}/healthcheck"
HEALTHCHECK_URL="${HEALTHCHECK_URL:-$DEFAULT_HEALTHCHECK_URL}"
git checkout master
git reset --hard HEAD
git clean -fd
git fetch origin
git pull --ff-only origin master
source .venv/bin/activate
uv sync
python manage.py check
python manage.py migrate --noinput
python manage.py collectstatic --noinput
sudo systemctl restart petrovich
for ((attempt=1; attempt<=HEALTHCHECK_ATTEMPTS; attempt++)); do sudo systemctl is-active --quiet petrovich; done
for ((attempt=1; attempt<=HEALTHCHECK_ATTEMPTS; attempt++)); do curl --fail "$HEALTHCHECK_URL"; done
```

Important: this script is destructive to local uncommitted changes and is clearly intended only for the production host.

The script now also performs Django system checks before migrations, verifies that the `petrovich`
systemd unit becomes active after restart, and retries the local `/healthcheck` endpoint with `curl`
until it returns HTTP 200. The healthcheck target defaults to `127.0.0.1:10010` but will follow
`GUNICORN_BIND_PORT` from `.env` when present; the script intentionally uses loopback instead of the
gunicorn bind address so it still works when gunicorn listens on `0.0.0.0`. `HEALTHCHECK_URL` can
also be overridden explicitly from the shell environment before running the script.

The repository now contains gunicorn app-server configuration in `config/gunicorn/gunicorn.conf.py`, reads `.env`,
binds Django using `GUNICORN_BIND_ADDRESS` + `GUNICORN_BIND_PORT` (defaults `127.0.0.1` and `10010`),
and no longer depends on `uWSGI`.

---

## Validation guidance for AI agents

Because the repo has broad functionality and light automated coverage, validate conservatively.

## When changing pure parsing / helper logic

Start with:

```bash
python manage.py test
```

If the touched area has no tests, explain that explicitly in your final summary.

## When changing models

- inspect existing models and migrations first
- create migrations if needed
- verify migration impact carefully

Typical checks:

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py test
```

## When changing Telegram response behavior

Check carefully for:

- message length chunking
- parse mode / formatting differences
- attachment size limits
- edit vs send behavior
- reply/thread metadata
- deletion of original messages

## When changing scheduled/reminder flows

Check both:

- the model / persistence side
- the management command execution side

## When changing GPT flows

Check carefully for:

- reply-chain history reconstruction
- cached message usage in Redis
- provider/model selection
- encrypted API key handling
- long-response fallback to file attachments

## When changing media flows

Check carefully for:

- hostname matching
- attachment type assumptions
- cache vs direct send behavior
- file size limits
- automatic deletion of original user messages
- privileged paths such as `save_to_disk`

---

## Conventions and patterns to preserve

## 1. The command registry is authoritative

If you add or remove behavior, check:

- `apps/commands/registry.py`
- command help text
- access role
- whether it should also participate in `registry_accept_extra_commands`

## 2. Help text is code-defined

There is no separate command documentation system. User help is built from command metadata.

If you change a command interface, update its `help_text`.

## 3. Russian-first UX

Most user-visible text is in Russian. Match the existing language unless explicitly asked otherwise.

## 4. Platform abstraction exists, but Telegram is the real implementation

The code has abstractions for platforms, but the practical implementation is Telegram-centric. Be cautious about making “generic” refactors unless you verify that abstraction is genuinely used.

## 5. Logging is structured

The project uses JSON logging with user/chat/message identifiers in `log_filter`. It allows filtering logs when calling the corresponding command to restrict access.

`petrovich/settings.py` reconfigures `stdout` and `stderr` to UTF-8 with `backslashreplace` and writes file logs with explicit UTF-8 encoding, so emoji and other non-CP1251 characters do not break local Windows logging.

---

## High-risk areas

These areas deserve extra caution:

## Secrets and credentials

- `.env`
- Fernet-encrypted GPT keys
- Telegram/GitHub/ImgBB credentials

## Production-coupled infrastructure assumptions

- hardcoded LAN addresses in settings/provider code
- local Telegram server mode
- domain assumptions around `andrewsha.net`

## Telegram side effects

- message edits
- message deletions
- media groups
- callback payload size constraints
- parse-mode/markup handling

## GitHub side effects

- issue creation
- comment creation
- webhook-triggered user notifications

## Machine-level side effects

- `sudo systemctl` usage for Minecraft
- disk writes in media save paths

## Large integration-heavy modules

- GPT command utilities
- media services/parsers
- Telegram sending/editing code

Prefer targeted fixes over broad refactors in these areas.

---

## Safe workflow for AI agents

## Before editing

1. Read the relevant architecture path from ingress to command/output.
2. Identify whether the change touches:
   - bot core
   - event core
   - command registry
   - DB models
   - external APIs
   - message formatting/sending
   - scheduled/background execution
3. Check for hidden side effects such as:
   - auto-triggered commands
   - webhook callbacks
   - Redis reply-chain behavior
   - file writes / message deletion / external requests

## During editing

- Keep changes narrow.
- Preserve Russian UX style where relevant.
- Update help text if command usage changes.
- Update registry entries if command exposure changes.
- Add or update migrations only when required.
- Avoid infrastructure “cleanup” unless explicitly requested.

## After editing

- Run the safest relevant validation you can.
- State clearly what you validated and what you could not validate.
- Call out any assumptions involving env vars, Redis, Telegram, or external APIs.

---

## Known ambiguities and stale-looking areas

Document these carefully rather than treating them as confirmed bugs:

1. `config/setup/setup.sh` is a Linux bootstrap script using `uv`; local Windows debugging is better served by `.env` plus `docker-compose.local.yml` for PostgreSQL/Redis.
2. GitHub Actions workflow is named as CI, but the active job is effectively deployment; test steps are commented out.
3. README is intentionally sparse and points to an external wiki, so local repo docs are incomplete by design.
4. ASGI exists, but the visible deployment shape is WSGI/gunicorn-oriented.

Do not “fix” these unless explicitly asked.

---

## Recommended starting points by task type

## Add or modify a bot command

Read:

- `apps/commands/command.py`
- `apps/commands/registry.py`
- the target command module
- any related models/helpers/connectors

Then verify:

- registry inclusion
- help text
- access rules
- mention / PM / attachment behavior

## Change Telegram send/edit behavior

Read:

- `apps/bot/core/bot/bot.py`
- `apps/bot/core/bot/telegram/tg_bot.py`
- `apps/bot/core/messages/`

## Change GPT behavior

Read:

- `apps/commands/gpt/commands_utils/gpt/gpt_abstract.py`
- relevant provider API file
- `apps/commands/gpt/models.py`
- cache/reply-chain behavior in `apps/shared/utils/cache.py` and `apps/bot/core/event/event.py`

## Change reminder behavior

Read:

- `apps/commands/notifies/models.py`
- `apps/commands/notifies/services.py`
- `apps/commands/notifies/management/commands/check_notify.py`
- `apps/commands/notifies/commands/notifies.py`

## Change media behavior

Read:

- `apps/commands/media_command/commands/media_command.py`
- `apps/commands/media_command/service.py`
- the service implementation for the relevant hostname

## Change GitHub issue/reply behavior

Read:

- `apps/commands/other/commands/issue.py`
- `apps/commands/other/commands/service/github_reply.py`
- `apps/bot/views.py`
- `apps/connectors/api/github/`

---

## Final mental model

Think of this repository as:

- a **Telegram bot platform layer**
- plus a **registry of bot commands**
- plus several **stateful feature subsystems**
- plus a handful of **production-specific integrations and operational shortcuts**

The safest way to work here is to trace the full path of a feature before editing it:

**webhook -> event -> routing -> command -> response -> Telegram/API side effects -> persistence/cache**

If you preserve that mental model, you will usually edit the right place and avoid the most dangerous regressions.
