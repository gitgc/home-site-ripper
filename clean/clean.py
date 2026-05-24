#!/usr/bin/env python3
"""
Strip tracking, SEO, and WordPress noise from ripped HTML files.
Downloads Ruffle locally and injects it only on pages with Flash content.
Requires: pip install beautifulsoup4

Usage:
    python3 clean.py [site_dir] [glob]
    python3 clean.py /site "[Ss][Cc]*/*.html"
"""

import io
import json
import os
import re
import sys
import urllib.request
import zipfile
from pathlib import Path
from urllib.parse import urlparse
from bs4 import BeautifulSoup, Comment

RUFFLE_API = 'https://api.github.com/repos/ruffle-rs/ruffle/releases/latest'
RUFFLE_DIR = '_ruffle'
RUFFLE_SCRIPT_SRC = f'/{RUFFLE_DIR}/ruffle.js'


def ensure_ruffle(site_dir: Path) -> None:
    ruffle_dir = site_dir / RUFFLE_DIR
    if (ruffle_dir / 'ruffle.js').exists():
        return

    print('Fetching latest Ruffle release info...')
    req = urllib.request.Request(RUFFLE_API, headers={'User-Agent': 'clean.py'})
    with urllib.request.urlopen(req) as r:
        release = json.loads(r.read())

    asset = next(
        a for a in release['assets']
        if 'selfhosted' in a['name'] and a['name'].endswith('.zip')
    )
    print(f'Downloading Ruffle {release["tag_name"]}...')
    with urllib.request.urlopen(asset['browser_download_url']) as r:
        zf = zipfile.ZipFile(io.BytesIO(r.read()))

    ruffle_dir.mkdir(exist_ok=True)
    zf.extractall(ruffle_dir)
    print(f'Ruffle installed to {ruffle_dir}')


def has_flash(soup: BeautifulSoup) -> bool:
    return bool(
        soup.find('embed', type=re.compile(r'shockwave-flash', re.I)) or
        soup.find('embed', src=re.compile(r'\.swf', re.I)) or
        soup.find('object', data=re.compile(r'\.swf', re.I))
    )


def clean(html: str, source_host: str) -> tuple[str, list[str]]:
    soup = BeautifulSoup(html, 'html.parser')
    removed = []

    def drop(tag, reason):
        tag.decompose()
        removed.append(reason)

    # -- Google Analytics / MonsterInsights ----------------------------------

    for tag in soup.find_all('script', src=re.compile(r'googletagmanager\.com')):
        drop(tag, 'GTM script tag')

    for tag in soup.find_all('script', src=re.compile(r'google-analytics-for-wordpress')):
        drop(tag, 'MonsterInsights script tag')

    for tag in soup.find_all('script', attrs={'data-cfasync': 'false', 'data-wpfc-render': 'false'}):
        drop(tag, 'GA/MonsterInsights inline script block')

    # -- SEO Framework comment block -----------------------------------------

    for node in soup.find_all(string=lambda t: isinstance(t, Comment) and 'SEO Framework' in t):
        node.extract()
        removed.append('SEO Framework comment')

    # -- SEO meta / link tags ------------------------------------------------

    for tag in soup.find_all('link', rel='canonical'):
        drop(tag, 'canonical link')

    for tag in soup.find_all('meta', property=re.compile(r'^og:')):
        drop(tag, f'og: meta ({tag.get("property")})')

    for tag in soup.find_all('meta', attrs={'name': re.compile(r'^twitter:')}):
        drop(tag, f'twitter: meta ({tag.get("name")})')

    for tag in soup.find_all('meta', attrs={'name': 'google-site-verification'}):
        drop(tag, 'Google site verification meta')

    for tag in soup.find_all('script', type='application/ld+json'):
        drop(tag, 'ld+json schema script')

    # -- External fonts ------------------------------------------------------

    for tag in soup.find_all('link', href=re.compile(r'fonts\.googleapis\.com')):
        drop(tag, 'Google Fonts link')

    for tag in soup.find_all('link', href=re.compile(r'fonts\.gstatic\.com')):
        drop(tag, 'gstatic preconnect')

    for tag in soup.find_all('link', rel='dns-prefetch', href=re.compile(r'fonts\.googleapis\.com')):
        drop(tag, 'Google Fonts dns-prefetch')

    # -- WordPress feed / API / oEmbed discovery links -----------------------

    for tag in soup.find_all('link', type='application/rss+xml'):
        drop(tag, 'RSS feed link')

    for tag in soup.find_all('link', rel=lambda r: r and 'https://api.w.org/' in r):
        drop(tag, 'WP REST API link')

    for tag in soup.find_all('link', type='application/json+oembed'):
        drop(tag, 'oEmbed JSON link')

    for tag in soup.find_all('link', type='text/xml+oembed'):
        drop(tag, 'oEmbed XML link')

    for tag in soup.find_all('link', href=re.compile(r'wp-json'), type='application/json'):
        drop(tag, 'WP JSON API link')

    for tag in soup.find_all('link', rel='EditURI'):
        drop(tag, 'EditURI / xmlrpc link')

    # -- Remaining external tags pointing to the source domain ---------------

    host_re = re.compile(re.escape(source_host))
    for tag in soup.find_all(['link', 'script'], href=host_re):
        drop(tag, f'external {source_host} {tag.name}')

    for tag in soup.find_all('script', src=host_re):
        drop(tag, f'external {source_host} script')

    for tag in soup.find_all('script', src=re.compile(r'www\.google\.com/recaptcha')):
        drop(tag, 'Google reCAPTCHA script')

    # -- Ajax Search Lite: swap widget for a plain search form ---------------
    # ASL needs a live WordPress AJAX backend; replace with a GET form that
    # submits to /search.html (Pagefind), preserving the header layout.

    for tag in soup.find_all('div', class_='asl_w_container'):
        form = soup.new_tag('form', action='/search.html', method='get')
        form['style'] = 'display:inline-flex;gap:.4rem;align-items:center'

        inp = soup.new_tag('input', type='search', name='q')
        inp['placeholder'] = 'Search manual…'
        inp['autocomplete'] = 'off'
        inp['style'] = (
            'padding:.3rem .6rem;font-size:.9rem;'
            'border:1px solid #aaa;border-radius:3px;width:14rem'
        )

        btn = soup.new_tag('button', type='submit')
        btn['style'] = (
            'padding:.3rem .7rem;font-size:.9rem;cursor:pointer;'
            'border-radius:3px;border:1px solid #aaa;background:#fff'
        )
        btn.string = 'Search'

        form.append(inp)
        form.append(btn)
        tag.replace_with(form)
        removed.append('Ajax Search Lite widget → /search.html form')

    # -- Sidebar widgets containing links back to the source domain ----------

    for tag in soup.find_all('div', class_='widget'):
        if tag.find('a', href=host_re):
            drop(tag, f'sidebar widget with external {source_host} link')

    # -- Empty comments block ------------------------------------------------

    comments = soup.find('div', id='comments')
    if comments and not comments.get_text(strip=True):
        drop(comments, 'empty comments div')

    # -- Ruffle: swap to local if page has Flash, otherwise remove -----------

    ruffle_re = re.compile(r'unpkg\.com/@ruffle')
    page_has_flash = has_flash(soup)

    for tag in soup.find_all('script', src=ruffle_re):
        if page_has_flash:
            tag['src'] = RUFFLE_SCRIPT_SRC
            removed.append(f'Ruffle: swapped to local {RUFFLE_SCRIPT_SRC}')
        else:
            drop(tag, 'Ruffle script (no Flash content)')

    if page_has_flash and not soup.find('script', src=RUFFLE_SCRIPT_SRC):
        new_tag = soup.new_tag('script', src=RUFFLE_SCRIPT_SRC)
        soup.head.append(new_tag)
        removed.append(f'Ruffle: injected {RUFFLE_SCRIPT_SRC}')

    # -- WordPress inline <style> blocks by id -------------------------------

    for sid in (
        'wp-emoji-styles-inline-css',
        'wp-block-library-inline-css',
        'classic-theme-styles-inline-css',
        'global-styles-inline-css',
        'wp-img-auto-sizes-contain-inline-css',
        'wpdreams-asl-basic-inline-css',
    ):
        tag = soup.find('style', id=sid)
        if tag:
            drop(tag, f'<style id="{sid}">')

    # -- WordPress inline <script> blocks by id ------------------------------

    for sid in (
        'wp-emoji-settings',
        'monsterinsights-frontend-script-js-extra',
        'contact-form-7-js-before',
        'wd-asl-ajaxsearchlite-js-before',
        'wpcf7-recaptcha-js-before',
    ):
        tag = soup.find('script', id=sid)
        if tag:
            drop(tag, f'<script id="{sid}">')

    for tag in soup.find_all('script', type='speculationrules'):
        drop(tag, 'speculation rules script')

    for tag in soup.find_all('script', type='module'):
        if tag.string and 'wp-emoji-loader' in tag.string:
            drop(tag, 'WP emoji loader module')

    return str(soup), removed


def main() -> None:
    site_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('site')
    glob_pat = sys.argv[2] if len(sys.argv) > 2 else '[Ss][Cc]*/*.html'

    site_url = os.environ.get('SITE_URL', '')
    source_host = urlparse(site_url).netloc
    if not source_host:
        sys.exit('error: SITE_URL env var is not set or has no hostname')

    print(f'source host: {source_host}')

    if not site_dir.is_dir():
        sys.exit(f'error: {site_dir} is not a directory')

    ensure_ruffle(site_dir)

    files = sorted(site_dir.glob(glob_pat))
    if not files:
        sys.exit(f'error: no files matched {site_dir}/{glob_pat}')

    changed = unchanged = errors = 0

    for path in files:
        try:
            original = path.read_text(encoding='utf-8', errors='replace')
            cleaned, removed = clean(original, source_host)
            if removed:
                path.write_text(cleaned, encoding='utf-8')
                print(f'cleaned  {path.relative_to(site_dir)}')
                for item in removed:
                    print(f'         - {item}')
                changed += 1
            else:
                unchanged += 1
        except Exception as exc:
            print(f'error    {path}: {exc}', file=sys.stderr)
            errors += 1

    print(f'\n{changed} cleaned, {unchanged} unchanged, {errors} errors.')


if __name__ == '__main__':
    main()
