# ChopURL

ChopURL is a full-stack URL shortener built with FastAPI, Redis, Vue 3, and Supabase Auth. It supports public and authenticated shortening, custom aliases, owner-scoped link management, password reset, and click analytics.

![ChopURL home screen](imgg/chop.png)

## What It Does

- Creates public anonymous short links or links owned by an authenticated Supabase user.
- Accepts custom aliases with server-side validation and reserved-route protection.
- Deduplicates automatically generated links within one owner context only. Anonymous links and different users receive separate links for the same destination.
- Redirects `/{short_code}` publicly and records aggregate clicks, last-click time, and the latest 50 click timestamps.
- Provides public aggregate statistics without the destination URL or history; detailed analytics are available only to the owner.
- Provides an authenticated dashboard with owner-scoped pagination, totals, deletion, and clear-all actions.
- Supports signup, login, logout, confirmation messaging, forgotten-password emails, and reset-password callbacks through Supabase.
- Applies configurable Redis-backed fixed-window rate limits and daily creation quotas.

This is a single-service portfolio project. It does not claim distributed storage, fault tolerance, malware scanning, benchmarked latency, or production deployment.

## Stack And Architecture

| Layer | Technology |
| --- | --- |
| API | FastAPI, Pydantic, PyJWT, httpx |
| Data | Redis 7, redis-py asyncio |
| Frontend | Vue 3, Vite, Vue Router, Axios |
| Authentication | Supabase Auth |
| Testing | pytest, Vitest, Vue Test Utils |
| Local containers | Docker Compose, Redis, Nginx |

The backend is organized into API routes, authentication/configuration, a Redis link service, schemas, and utilities. The Vue app has dedicated API, auth, routing, component, and view layers. See [ARCHITECTURE.md](ARCHITECTURE.md) for request flows and Redis key design.

## Authentication And Authorization

The frontend obtains the latest Supabase session and adds its bearer token to API requests when one exists. Public shortening still works with no session. A supplied invalid or expired bearer token is rejected rather than being treated as anonymous.

The backend verifies a token locally when `SUPABASE_JWT_SECRET` is configured; otherwise it verifies the session through Supabase's user endpoint. The authenticated user ID controls ownership:

- `GET /api/v1/admin/links`, deletion, clear-all, and `/api/v1/auth/me` require authentication.
- A user can list, delete, and see detailed analytics only for their own links.
- `GET /api/v1/stats/{short_code}` remains public, but returns only the code, short URL, and aggregate click count for non-owners.
- Anonymous links have no owner-only analytics view.

## Public And Protected Endpoints

| Endpoint | Access | Behavior |
| --- | --- | --- |
| `GET /health/live` | Public | Process liveness only. |
| `GET /health` and `GET /health/ready` | Public | Redis readiness check; returns `503` when Redis is unavailable. |
| `POST /api/v1/shorten` | Public or authenticated | Creates an anonymous or owned link. |
| `GET /{short_code}` | Public | HTTP 302 redirect and click recording. |
| `GET /api/v1/{short_code}` | Public | Returns the redirect destination as JSON and records a click. |
| `GET /api/v1/stats/{short_code}` | Public or owner | Redacted public statistics or owner detail. |
| `/api/v1/admin/links*` | Authenticated owner | Paginate, delete, or clear only the caller's links. |
| `GET /api/v1/auth/me` | Authenticated | Returns the verified user ID. |

## Local Setup

### Prerequisites

- Python 3.11+ (CI and Docker use Python 3.13)
- Node.js 20+ (required by the installed Supabase JavaScript SDK)
- Redis 7+ or Docker
- A Supabase project when testing authentication flows

### 1. Start Redis

With Docker:

```bash
docker compose up redis
```

Or with a local installation:

```bash
redis-server
redis-cli ping
```

`redis-cli ping` should return `PONG`.

### 2. Configure And Run The Backend

```bash
cd backend
python3 -m venv ../.venv
source ../.venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API is available at `http://localhost:8000`; interactive OpenAPI documentation is at `http://localhost:8000/docs`.

### 3. Configure And Run The Frontend

```bash
cd admin
npm ci
cp .env.example .env
npm run dev
```

Vite prints the local URL, normally `http://localhost:5173`.

### Docker Compose

`docker compose up --build` runs Redis, the FastAPI API on port 8000, and the built Vue app through Nginx on port 5173. Provide Supabase variables in a local root `.env` file or export them before building; this file is not committed.

## Environment Variables

Copy the tracked examples before adding local values:

```bash
cp backend/.env.example backend/.env
cp admin/.env.example admin/.env
```

### Backend

| Variable | Required | Purpose |
| --- | --- | --- |
| `REDIS_URL` | Yes | Redis connection URL. |
| `APP_NAME` | No | FastAPI documentation title; defaults to `ChopURL`. |
| `DEBUG` | No | FastAPI debug mode; keep `false` in production. |
| `BASE_URL` | Yes | Public base URL used in generated links. |
| `ALLOWED_ORIGINS` | Yes in browser deployments | JSON array of allowed frontend origins. |
| `SHORT_URL_LENGTH` | No | Generated alias length; defaults to `6`. |
| `SUPABASE_URL` | For authentication | Supabase project URL for fallback token verification. |
| `SUPABASE_ANON_KEY` | For authentication | Supabase anon/public key used for fallback verification. |
| `SUPABASE_JWT_SECRET` | Recommended for authentication | HS256 JWT secret for local verification. |
| `BLOCKED_HOSTS` | No | JSON array of destination hosts/subdomains to reject. |
| `USER_CREATE_LIMIT_PER_DAY` | No | Authenticated creation quota; defaults to `100`. |
| `ANONYMOUS_CREATE_LIMIT_PER_DAY` | No | Per-IP anonymous creation quota; defaults to `20`. |
| `SHORTEN_RATE_LIMIT` | No | Per-IP fixed-window shorten limit; defaults to `10/minute`. |
| `REDIRECT_RATE_LIMIT` | No | Per-IP fixed-window redirect limit; defaults to `120/minute`. |
| `STATS_RATE_LIMIT` | No | Per-IP fixed-window stats limit; defaults to `60/minute`. |
| `ADMIN_RATE_LIMIT` | No | Per-IP fixed-window admin limit; defaults to `60/minute`. |

### Frontend

| Variable | Required | Purpose |
| --- | --- | --- |
| `VITE_API_BASE_URL` | For separate API/frontend deployments | API base URL. In development it defaults to `http://localhost:8000/api/v1`; production falls back to same-origin `/api/v1`. |
| `VITE_SUPABASE_URL` | For authentication | Supabase project URL. |
| `VITE_SUPABASE_ANON_KEY` | For authentication | Supabase anon/public key. |

Never commit `.env` files, service-role keys, JWT secrets, or Redis credentials. The anon key is designed for browser use but should still be limited by Supabase project configuration.

## Supabase And Password Reset

Create a Supabase project, enable email/password authentication, and copy its URL and anon key into both local environment files. Set `SUPABASE_JWT_SECRET` in the backend when local HS256 verification is desired.

Add the deployed frontend callback URL, plus local development callbacks, to Supabase Auth redirect URLs:

```text
http://localhost:5173/login?mode=reset
http://127.0.0.1:5173/login?mode=reset
https://your-frontend.example/login?mode=reset
```

The app sends reset emails back to `/login?mode=reset`. Email confirmation behavior is controlled by the Supabase project settings.

## API Examples

Create an anonymous link:

```bash
curl -X POST http://localhost:8000/api/v1/shorten \
  -H 'Content-Type: application/json' \
  -d '{"url":"https://example.com/docs","custom_code":"example-docs"}'
```

Create or manage an owned link by supplying a Supabase access token:

```bash
curl 'http://localhost:8000/api/v1/admin/links?skip=0&limit=8' \
  -H 'Authorization: Bearer <supabase-access-token>'
```

Public statistics are intentionally redacted:

```bash
curl http://localhost:8000/api/v1/stats/example-docs
```

The owner can use the same endpoint with a bearer token to receive the original URL, timestamps, and recent click history.

## Rate Limits And Destination Checks

SlowAPI stores fixed-window per-IP rate-limit counters in Redis. Creation also has separate per-user or per-IP daily quotas. Limit values are environment-configurable and requests above a route limit return HTTP `429`.

Custom aliases must be 3-32 characters using letters, numbers, `_`, or `-`; leading/trailing whitespace and reserved route names are rejected. Destination validation rejects URLs with embedded credentials, localhost, literal private/reserved IP addresses, and configured blocked hosts.

These are basic controls only. ChopURL does not scan destinations for malware, resolve hostnames to block every private-network target, provide reporting/disable workflows, or enforce organization-level quotas.

## Development Commands

Backend:

```bash
cd backend
../.venv/bin/python -m pytest -q
../.venv/bin/python -m pip check
```

Frontend:

```bash
cd admin
npm run lint
npm test
npm run test:coverage
npm run type-check
npm run build
```

GitHub Actions runs the backend pytest suite and frontend lint, tests, type-check, and build on pushes and pull requests.

## Deployment Status And Limitations

Docker Compose has been validated for local development. No production deployment target, benchmark, high-availability topology, replication strategy, or managed monitoring setup is configured in this repository.

Redis is the only data store, so Redis data loss removes links and analytics. Click totals are atomically incremented in Redis, but analytics remain request-path work and there is no durable event stream or background processing. See [ARCHITECTURE.md](ARCHITECTURE.md) for the current design and realistic next steps.

## Security

See [SECURITY.md](SECURITY.md) for reporting guidance, trust boundaries, secret handling, and known limitations. See [CONTRIBUTING.md](CONTRIBUTING.md) for development and pull-request expectations.

## License

This repository does not currently include a license file.

Built by Jyothsna Karuparthi.
