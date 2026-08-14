# IROH website redesign files

Copy these files into the corresponding locations in `leb-irohpodcast/irohsite`:

- `_config.yml` replaces the existing configuration.
- `index.md` replaces the existing homepage.
- `archive.md` is new.
- `_includes/iroh-masthead.html` is new.
- `_includes/header.html` replaces Minima's text-only site header with the HBI utility strip.
- `_includes/head.html` adds podcast-feed discovery, social metadata support and site icons.
- `_includes/footer.html` replaces Minima's stock footer.
- `assets/main.scss` is new and automatically replaces Minima's stock stylesheet.
- `_images/IROH_SocialLogo.png` supplies the compact header mark.
- `scripts/sync_podcast.py` replaces the existing RSS synchronization script.
- `.github/workflows/sync-podcast.yml` replaces the existing workflow.
- `robots.txt` points search engines to the generated sitemap.

Commit the workflow file last. Then manually run **Sync podcast and deploy website** from the repository's Actions tab.

The first run will create local transcript pages for every RSS item with a Pinecast transcript link. Later runs create a page only for a newly published transcript. To deliberately rebuild existing transcript pages, run the script with `REFRESH_TRANSCRIPTS=1` in the environment.

The `_config.yml` `include` entry is required because Jekyll normally excludes directories whose names begin with an underscore. It makes the existing `_images` directory available on the built website.

## Instagram Picture Wire automation

The homepage gallery is rendered from `_data/instagram_posts.json`. Its image
previews are cached under `_images/instagram`, so visitors do not need to load
Instagram's embed script and the gallery can retain the site's period styling.

Automatic updates use Meta's official Instagram API:

1. Make sure `@iroh_show` is an Instagram professional account (Creator or Business).
2. In a Meta app, add **Instagram API with Instagram Login** and authorize the IROH account with the `instagram_business_basic` permission.
3. Add the resulting long-lived token as the repository Actions secret `INSTAGRAM_ACCESS_TOKEN`.
4. If the Meta app requires an explicit Graph API version, add it as the repository variable `INSTAGRAM_API_VERSION`; otherwise leave the variable unset.
5. Run **Refresh Instagram Picture Wire** once from the Actions tab.

The workflow checks every six hours, commits new gallery data and cached
previews, and deploys only when something changed. If the secret is not set,
the seeded gallery stays online and the workflow exits without changing it.
Meta controls access-token lifetimes, so renew the secret before its token
expires.
