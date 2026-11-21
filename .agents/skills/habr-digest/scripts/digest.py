"""Collect the Russian Habr feed and its current reading sidebar."""

import argparse
import json
import re
import sqlite3
import sys
from contextlib import closing
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urljoin, urlsplit
from urllib.request import Request, urlopen


FEED_URL = "https://habr.com/ru/articles/"
POPULAR_URL = "https://habr.com/kek/v2/articles/most-reading?hl=ru&fl=ru"
SIDEBAR_SIZE = 5  # Habr's article-list-block renders the first five API results.
STATE_PATH = Path(__file__).resolve().parents[4] / "state.sqlite3"


@dataclass(frozen=True)
class Article:
    id: str
    published: datetime
    title: str
    score: int
    url: str


@dataclass(frozen=True)
class Checkpoint:
    published: datetime
    ids: frozenset[str]


class FeedChanged(ValueError):
    """The listing changed while paginating through it."""


def timestamp(value):
    result = datetime.fromisoformat(value)
    if result.utcoffset() is None:
        raise ValueError("Habr supplied a timestamp without a timezone.")
    return result.astimezone(UTC)


def fetch(url):
    request = Request(url, headers={"Cache-Control": "no-cache"})
    with urlopen(request, timeout=15) as response:
        return response.read().decode("utf-8")


class FeedPage(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.articles = []
        self.next_href = None
        self.card = None
        self.field = None
        self.feed(html)
        self.close()
        if self.card is not None or not self.articles:
            raise ValueError("Could not read the article cards from the Habr feed.")
        if any(a.published < b.published for a, b in zip(self.articles, self.articles[1:])):
            raise ValueError("The Habr feed is not sorted from newer to older.")

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        classes = attrs.get("class", "").split()
        if tag == "a" and attrs.get("id") == "pagination-next-page":
            self.next_href = urljoin(FEED_URL, attrs["href"])
        if tag == "article" and "tm-articles-list__item" in classes:
            self.card = {"id": attrs["id"], "title": "", "score": ""}
        if self.card is None:
            return
        if tag == "time" and "datetime" in attrs:
            self.card.setdefault("published", attrs["datetime"])
        if tag == "a" and "tm-title__link" in classes:
            self.card["url"] = urljoin(FEED_URL, attrs["href"])
            self.field = ("title", "a")
        if tag == "span" and "tm-votes-meter__value_rating" in classes:
            self.field = ("score", "span")

    def handle_data(self, data):
        if self.card is not None and self.field is not None:
            self.card[self.field[0]] += data

    def handle_endtag(self, tag):
        if self.field is not None and self.field[1] == tag:
            self.field = None
        if tag == "article" and self.card is not None:
            title = self.card["title"].strip()
            if not title:
                raise ValueError("An article in the Habr feed is missing its title.")
            self.articles.append(Article(
                self.card["id"], timestamp(self.card["published"]), title,
                int(self.card["score"].replace("−", "-")), self.card["url"],
            ))
            self.card = None
            self.field = None


class TitleText(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.parts = []
        self.feed(html)
        self.close()

    def handle_data(self, data):
        self.parts.append(data)


def read_sidebar():
    data = json.loads(fetch(POPULAR_URL))
    ids = data["articleIds"][:SIDEBAR_SIZE]
    if not ids:
        raise ValueError("Habr returned an empty reading sidebar.")
    articles = []
    for article_id in ids:
        item = data["articleRefs"][article_id]
        title = "".join(TitleText(item["titleHtml"]).parts).strip()
        score = item["statistics"]["score"]
        if not title or type(score) is not int or not article_id.isascii() or not article_id.isdigit():
            raise ValueError("Habr returned an incomplete article in the reading sidebar.")
        articles.append(Article(article_id, timestamp(item["timePublished"]), title, score,
                                f"https://habr.com/{item['lang']}/articles/{article_id}/"))
    return articles


def collect_feed(previous, now):
    first = FeedPage(fetch(FEED_URL))
    results = list(first.articles)
    seen = {article.id for article in results}
    newest = results[0].published
    newest_ids = frozenset(article.id for article in results if article.published == newest)
    if previous and newest < previous.published:
        raise ValueError("The Habr feed returned an older snapshot than the saved checkpoint.")
    if previous and newest == previous.published:
        newest_ids |= previous.ids

    boundary = previous or Checkpoint(now - timedelta(hours=24), frozenset())
    if previous and seen & previous.ids:
        return results, Checkpoint(newest, newest_ids)

    page = first
    visited = {FEED_URL}
    while page.articles[-1].published >= boundary.published:
        next_page = page.next_href
        if not next_page:
            raise ValueError("Habr pagination ended before the saved time boundary was reached.")
        parsed = urlsplit(next_page)
        if (next_page in visited or parsed.scheme != "https" or parsed.netloc != "habr.com"
                or not re.fullmatch(r"/ru/articles/page[0-9]+/", parsed.path)):
            raise ValueError("Habr returned an unexpected next-page link.")
        visited.add(next_page)
        page = FeedPage(fetch(next_page))
        for article in page.articles:
            if article.published < boundary.published:
                break
            if article.id not in seen and article.id not in boundary.ids and article.score >= 2:
                results.append(article)
            seen.add(article.id)
            if article.published == newest:
                newest_ids |= {article.id}

    if len(visited) > 1:
        latest_first = FeedPage(fetch(FEED_URL))
        if [article.id for article in latest_first.articles] != [article.id for article in first.articles]:
            raise FeedChanged("The Habr feed changed while the collector was reading older pages.")

    return results, Checkpoint(newest, newest_ids)


def render_section(heading, articles):
    lines = [f"## {heading}", ""]
    for article in articles:
        title = re.sub(r"\s+", " ", article.title)
        title = re.sub(r"([\\`*_\[\]<>~&])", r"\\\1", title)
        score = f"{article.score:+d}" if article.score else "0"
        lines.append(f"- {title} · {score} · [ссылка]({article.url})")
    return "\n".join(lines)


def run(state_path, now):
    with closing(sqlite3.connect(state_path, timeout=20)) as db, db:
        db.execute("BEGIN IMMEDIATE")
        db.execute("""
            CREATE TABLE IF NOT EXISTS checkpoint (
                singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
                published TEXT NOT NULL,
                article_ids TEXT NOT NULL
            )
        """)
        row = db.execute("SELECT published, article_ids FROM checkpoint WHERE singleton = 1").fetchone()
        previous = Checkpoint(timestamp(row[0]), frozenset(json.loads(row[1]))) if row else None
        try:
            feed, newest = collect_feed(previous, now)
        except FeedChanged:
            feed, newest = collect_feed(previous, now)
        sidebar = read_sidebar()
        digest = "\n\n".join((render_section("Новые статьи", feed),
                              render_section("Читают сейчас", sidebar)))
        db.execute("""
            INSERT INTO checkpoint VALUES (1, ?, ?)
            ON CONFLICT(singleton) DO UPDATE SET published = excluded.published,
                article_ids = excluded.article_ids
        """, (newest.published.isoformat(), json.dumps(sorted(newest.ids))))
    return digest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", type=Path, default=STATE_PATH, help="Use a separate checkpoint file.")
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    try:
        print(run(args.state, datetime.now(UTC)))
    except (URLError, OSError, ValueError, KeyError, TypeError, sqlite3.Error) as error:
        print(f"Habr digest: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
