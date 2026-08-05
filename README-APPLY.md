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
