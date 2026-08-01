# Architecture

ChopURL is a single FastAPI service with Redis as its only application data store and a separate Vue single-page application. Supabase Auth issues the frontend session tokens; the FastAPI service owns authorization decisions for link-management APIs.

## Request Flow

1. The Vue form submits `POST /api/v1/shorten`. Axios attaches the latest Supabase bearer token only when a session exists.
2. FastAPI optionally verifies the token and passes the user ID, or `None` for an anonymous request, to `LinkService`.
3. The service validates the destination and custom code. Generated aliases are deduplicated only within the same owner context.
4. Redis `SET ... NX` reserves the short-code record. The service then writes reverse lookup, owner index, expiry index, statistics, and summary records.
5. The API returns the generated short URL. Redis failures are surfaced through controlled `503` responses rather than empty data.

## Redirect Flow

1. A browser requests `GET /{short_code}`.
2. FastAPI reads `short:{short_code}` from Redis. Missing or expired records return `404`.
3. A Redis transaction increments the hash counter, updates the last-click time, prepends a history event, trims history to 50 entries, refreshes relevant TTLs, and increments the owner summary.
4. The browser receives an HTTP `302` response to the stored destination. The API equivalent, `GET /api/v1/{short_code}`, returns the destination as JSON for clients that need it.

## Authentication And Ownership Flow

The Vue client uses Supabase Auth for signup, login, logout, and password reset. The API reads the bearer token on every request that supplies one.

- With `SUPABASE_JWT_SECRET`, the backend verifies HS256 Supabase JWTs locally and requires audience `authenticated`.
- Without that secret, it calls Supabase's `/auth/v1/user` endpoint with the configured project URL and anon key.
- Admin routes require a verified user ID. The service checks the stored `user_id` before listing, deleting, clearing, or returning detailed analytics.
- Anonymous requests have the owner context `anonymous` and cannot appear in any user dashboard.

## Redis Data Model

`{owner}` is a Supabase user ID for authenticated records or `anonymous` for anonymous records.

| Key | Type | Purpose |
| --- | --- | --- |
| `short:{code}` | String JSON | Destination, creation time, and owner; expires after one year. |
| `url:{owner}:{original_url}` | String | Reverse lookup for automatically generated, owner-scoped deduplication; expires after one year. |
| `links_index:{owner}` | Sorted set | Code scored by creation timestamp for paginated dashboard reads. |
| `links_expiry:{owner}` | Sorted set | Code scored by expected expiry time for index cleanup. |
| `link_stats:{code}` | Hash | Atomic `clicks` counter and `last_clicked` timestamp. |
| `click_history:{code}` | List | Most recent 50 click timestamps. |
| `links_summary:{owner}` | Hash | Cached `total_links` and `total_clicks` for dashboard totals. |
| `user_links:{user_id}` | Set | Compatibility index for existing authenticated records. |
| `create_quota:{key}:{date}` | String counter | Daily per-user or per-IP creation quota. |

Short-code, reverse-lookup, stats, and history data use a one-year TTL. Expiry entries are cleaned before dashboard pagination. The sorted indexes and summaries are Redis state rather than a durable database.

## Analytics Strategy

Click counting uses `HINCRBY` inside a Redis transaction, so concurrent redirects do not overwrite the counter. The same transaction records `last_clicked`, pushes a timestamp to the list, and trims the list to 50 entries. Public statistics expose only the short URL, code, and aggregate click count; the owner receives the destination and history.

## Failure Behavior

- `/health/live` checks only that the process can answer requests.
- `/health` and `/health/ready` issue a Redis `PING` and return a controlled `503` on Redis errors.
- Redis exceptions from application routes return a controlled `503` without raw exception text.
- Missing records return `404`; invalid tokens return `401`; invalid input returns `400` or Pydantic `422`; alias conflicts return `409`; rate limits and creation quotas return `429`.

## Scalability Limits And Future Direction

This deployment has one API process design and one Redis data store. Redis is both the redirect store and the analytics store, so data is not durable beyond Redis persistence and the redirect path also writes analytics. The repository includes Render and Vercel deployment configuration, but no production deployment, clustering, replica/failover setup, background worker, durable event queue, or benchmark result.

A production evolution could store links in PostgreSQL, use Redis as a redirect cache, publish click events to Redis Streams or a queue, aggregate analytics in background workers, and run separately scalable redirect and management services. Those are future architecture options, not implemented features.
