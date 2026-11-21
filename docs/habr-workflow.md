# Habr collection workflow

## Standalone browser page

Open `habr.html` directly from the project folder in a browser. The page needs internet access to Habr and its image host. It does not need a local server, installation, or an agent. On opening, it loads the newest available articles. Refresh reloads the feed from the top and also refreshes «Читают сейчас».

- The minimum rating defaults to +2 and accepts integer scores, including negatives. «Все рейтинги» allows every score. The selected filter applies from the first article onward.
- The default display size is 20 articles. Choose 10 or 20 and navigate with the numbered buttons or «Назад» and «Дальше». To fill each page, the collector keeps reading source pages in publication order until it has enough matching articles or reaches Habr's last page. Results fetched during the current browsing session also support backwards navigation.
- Article cards render the source title, available cover, formatted preview, rating, and publication time. «Читать далее» opens the article on Habr. The full «Читают сейчас» article list stays visible independently of the rating filter and feed page.
- Closing or reloading the file discards the current feed position and selections. The page has no read-history or checkpoint storage.

The browser collector reads `https://habr.com/kek/v2/articles/` with `queryType=articles`, `sort=rating`, `hl=ru`, `fl=ru`, and `perPage=20`. The tested responses were in reverse chronological order. The collector uses the API's publication IDs, scores, and `leadData` fields. On 2026-11-21, the API accepted requests from `file://` in Chrome. It reported 50 source pages of 20 articles and rejected page 51 with `PAGINATOR_LIMIT`. The interface follows the limit reported by Habr. Images load lazily, and preview formatting is copied through an allowlist of HTML elements and web URLs.

## Codex chat digest

Use `$habr-digest` in a Codex chat opened in this project. The skill entry point is `.agents/skills/habr-digest/SKILL.md`. Its standard-library Python collector fetches the article cards at `https://habr.com/ru/articles/`, follows the page's next link, and writes Markdown to standard output. Its rules include every article on the first source page and apply the +2 threshold to new articles from subsequent pages.

The root-level `state.sqlite3` stores the newest publication timestamp and the article IDs at that timestamp for the chat digest. Both sections must succeed before the transaction advances the checkpoint. If the feed's first page changes while reading older pages, the collector retries the pass once. A second change retains the previous checkpoint so the next request can read the same interval. For live verification, use `--state` with a separate SQLite path to preserve the user's checkpoint.

## Reading sidebar source

Both collectors use `https://habr.com/kek/v2/articles/most-reading?hl=ru&fl=ru`. On 2026-11-21, the rendered Habr sidebar showed the first five API articles in order, followed by an optional promotional link. The collectors use the article slots. If Habr changes the sidebar length or response, compare the outputs with the rendered page and adjust `HABR_SIDEBAR_SIZE` in `habr.html` and `SIDEBAR_SIZE` in the Python collector as needed.
