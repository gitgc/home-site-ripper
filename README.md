# home-site-ripper

Mirror any website once, commit the static files to git, and serve them locally over HTTP with Caddy.

## Architecture

- **ripper** — one-shot `wget` container (Docker Compose `rip` profile) that mirrors `SITE_URL` into `./site/`
- **indexer** — one-shot [Pagefind](https://pagefind.app/) container (`index` profile) that builds a full-text search index into `./site/_pagefind/`
- **caddy** — serves `./site/` at `http://localhost`; root serves `search.html`

## Setup

1. Copy the example env file and fill in your values:

   ```sh
   cp .env.example .env
   ```

   | Variable        | Description                                                                   |
   |-----------------|-------------------------------------------------------------------------------|
   | `SITE_URL`      | URL of the site to rip                                                        |
   | `PAGEFIND_GLOB` | Glob of pages to index in `./site/` (default: `[Ss][Cc]*/*.html`)             |

2. Rip the site:

   ```sh
   ./scripts/rip.sh
   ```

3. Build the search index:

   ```sh
   ./scripts/index.sh
   ```

4. Commit the mirror and index:

   ```sh
   git add site/
   git commit -m "add site mirror"
   ```

5. Start Caddy:

   ```sh
   docker compose up -d
   ```
