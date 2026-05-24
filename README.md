# home-site-ripper

Mirror any website once, commit the static files to git, and serve them locally over HTTP with Caddy.

## Architecture

- **ripper** — one-shot `wget` container (Docker Compose `rip` profile) that mirrors `SITE_URL` into `./site/`
- **indexer** — one-shot [Pagefind](https://pagefind.app/) container (`index` profile) that builds a full-text search index into `./site/_pagefind/`
- **cleaner** — one-shot Python container (`clean` profile) that cleans the mirrored site using `SITE_URL` and `PAGEFIND_GLOB`
- **caddy** — serves `./site/` at `http://localhost`; root serves `search.html`

## Setup

1. Copy the example env file and fill in your values:

    ```sh
    cp .env.example .env
    ```

    | Variable          | Description                                                                 |
    |-------------------|-----------------------------------------------------------------------------|
    | `SITE_URL`        | URL of the site to rip                                                      |
    | `WGET_CUT_DIRS`   | Leading URL path segments to strip when saving files (default: 0)           |
    | `PAGEFIND_GLOB`   | Glob of pages to index in `./site/` (default: `[Ss][Cc]*/*.html`)           |

2. Rip the site:

    ```sh
    ./scripts/rip.sh
    ```

3. (Optional) Clean the markup:

    ```sh
    ./scripts/clean.sh
    ```

    Strips tracking scripts, SEO tags, and WordPress noise from the mirrored HTML.
    Pages containing Flash (`.swf`) content automatically get a self-hosted copy of
    [Ruffle](https://ruffle.rs) injected — downloaded once to `site/_ruffle/` on first
    run.

4. Build the search index:

    ```sh
    ./scripts/index.sh
    ```

5. (Optional) Commit the mirror and index:

    ```sh
    # remove the site and index from .gitignore first!
    git add site/ index/
    git commit -m "add site mirror"
    ```

6. Start Caddy to serve the site at `http://localhost`:

    ```sh
    ./scripts/host.sh
    ```
