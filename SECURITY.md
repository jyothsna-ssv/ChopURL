# Security Policy

## Reporting A Vulnerability

Do not open a public issue for a suspected vulnerability or include credentials, tokens, or exploit details in a public report. Use GitHub private vulnerability reporting for this repository when it is available. If it is not available, contact the maintainer privately through the repository owner's GitHub profile with a concise description, impact, and reproduction steps.

The maintainer will acknowledge reports, assess impact, and coordinate a fix or disclosure timeline. No formal support window or security-release SLA is currently promised.

## Authentication And Authorization Boundaries

- Supabase Auth handles browser signup, sign-in, password reset, and session refresh.
- The FastAPI backend verifies supplied bearer tokens locally with `SUPABASE_JWT_SECRET` when configured, or through Supabase's user endpoint otherwise.
- Management routes require authentication and enforce stored link ownership. A non-owner cannot delete another user's link or receive another owner's detailed analytics.
- Public shortening is deliberately available without authentication. Anonymous links are not added to authenticated dashboards.
- Public statistics intentionally omit the original destination and click history. Anyone who knows a code can still see its aggregate click count.

## Rate Limiting And Input Controls

Redis-backed fixed-window limits protect shortening, redirects, statistics, and management endpoints. Creation also has daily per-user and per-IP quotas. These settings are configurable through environment variables and return HTTP `429` when exceeded.

Custom aliases are validated on the backend and protected by Redis atomic reservation. Destination validation rejects embedded credentials, localhost, literal private/reserved IP addresses, and configured blocked hosts.

## Secret Management

- Keep `.env` files, Redis credentials, Supabase service-role keys, JWT secrets, and private keys out of Git.
- Use `backend/.env.example` and `admin/.env.example` as templates only; they contain placeholders.
- Treat `VITE_*` values as frontend-visible. Only use Supabase's anon/public key there, never a service-role key.
- Rotate credentials if they are accidentally disclosed and remove them from active configuration. Do not rewrite shared Git history without coordinating with collaborators.

## Known Limitations

- ChopURL does not scan destinations for malware, phishing, or reputation.
- Hostnames are not DNS-resolved before redirect creation, so literal-IP checks do not prevent every private-network destination technique.
- Rate limits and quotas are basic abuse mitigation, not comprehensive anti-abuse controls.
- Redis is the sole application data store; there is no durable database, replication, failover, or managed secret store configured here.
- There is no public report/disable workflow for short links and no production deployment security posture to claim.
