# Habr Digest

A standalone dark-mode reader for the Russian-language [Habr article feed](https://habr.com/ru/articles/). It runs from one HTML file and loads articles directly from Habr.

## Open the reader

1. Select **Code → Download ZIP** on GitHub and extract the archive, or clone the repository.
2. Open `habr.html` in your browser. The page needs an internet connection to load the feed and covers.
3. Use **Рейтинг от** to set a minimum score, **Все рейтинги** to show every score, or **Обновить** to reload the newest articles.

The reader needs no installation, build, local web server, or Codex session. Use a current browser. The page was tested in Chrome directly from `file://`.

## How the feed works

- The minimum rating defaults to **+2** and applies from the first article onward. Negative thresholds are supported.
- Show **10 or 20** articles per page. Pagination fills each page with matching articles in publication order until Habr's feed ends.
- Cards show the original title, available cover, formatted preview, rating, and publication time. **Читать далее** opens the full article on Habr.
- **Читают сейчас** shows Habr's current sidebar articles independently of the feed filter.
- Each opening starts at the newest articles. The browser page keeps no reading history between openings.

## Optional Codex or command-line digest

Open the repository as a Codex project and invoke `$habr-digest`, or run the standard-library collector with Python 3.11 or newer.

```sh
python .agents/skills/habr-digest/scripts/digest.py
```

The command prints a Markdown digest and saves the last successful pass in a local `state.sqlite3` file. That checkpoint belongs to the command-line and chat workflows.

For the Habr sources, pagination details, and checkpoint behavior, see [the project workflow](docs/habr-workflow.md).
