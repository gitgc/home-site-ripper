# home-site-ripper

Mirror any website once, commit the static files to git, and serve them internally over HTTPS with Caddy.

## Architecture

- **ripper** — one-shot `wget` container (Docker Compose `rip` profile) that mirrors `SITE_URL` into `./site/`
- **caddy** — serves `./site/` over HTTPS at `SITE_HOSTNAME` via Cloudflare DNS challenge TLS

## Setup

1. Copy the example env file and fill in your values:

   ```sh
   cp .env.example .env
   ```

   | Variable          | Description                                        |
   |-------------------|----------------------------------------------------|
   | `CADDY_DNS_EMAIL` | Email for Let's Encrypt registration               |
   | `CF_AUTH_TOKEN`   | Cloudflare API token (DNS:Edit for your domain)    |
   | `SITE_HOSTNAME`   | Internal hostname to serve the mirror on           |
   | `SITE_URL`        | URL of the site to rip                             |

2. Rip the site:

   ```sh
   ./scripts/rip.sh
   ```

3. Commit the mirror:

   ```sh
   git add site/
   git commit -m "add site mirror"
   ```

4. Start Caddy:

   ```sh
   docker compose up -d
   ```

## DNS

Point `SITE_HOSTNAME` at your internal server via split-horizon DNS or a local override. Caddy will automatically obtain and renew a public TLS certificate via Cloudflare DNS challenge, so HTTPS works even on a private IP.
