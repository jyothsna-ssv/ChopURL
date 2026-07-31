# Contributing

## Setup

Follow the local setup instructions in [README.md](README.md). Use Python 3.11+ and Node.js 20+, copy the tracked environment examples to local `.env` files, and run Redis before starting the API.

## Branches

Create focused branches using one of these prefixes:

- `feature/` for user-facing additions
- `fix/` for bug fixes
- `docs/` for documentation-only changes
- `chore/` for maintenance
- `codex/` for Codex-authored branches

Do not rewrite shared history or force-push without explicit coordination.

## Development And Testing

Keep changes narrow, retain owner and anonymous-link boundaries, and update documentation when behavior changes.

```bash
cd backend
../.venv/bin/python -m pytest -q
```

```bash
cd admin
npm run lint
npm test
npm run type-check
npm run build
```

Run `npm run test:coverage` when changing frontend behavior. Use the existing Vue, FastAPI, and Redis patterns instead of introducing unrelated frameworks. There is no backend formatter or linter configured; follow the surrounding style and keep imports, names, and comments clear.

## Pull Requests

Before opening a pull request:

- Explain the user-visible or correctness impact.
- Include or update focused tests for changed behavior.
- Run the relevant backend and frontend commands above.
- Do not commit `.env` files, credentials, generated `dist/`, coverage reports, or local Redis data.
- Update `README.md`, `ARCHITECTURE.md`, or `SECURITY.md` when the contract, data model, or trust boundary changes.

Keep pull requests small enough to review and call out known follow-up work rather than implying it has shipped.
