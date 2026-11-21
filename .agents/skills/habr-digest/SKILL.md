---
name: habr-digest
description: Collect the on-demand Habr article digest and the current «Читают сейчас» sidebar in this project. Use when the user asks for new Habr articles, «новые статьи Хабра», or invokes $habr-digest.
---

# Habr digest

Run `python .agents/skills/habr-digest/scripts/digest.py` from the project root. Run it once per user request. The script fetches Habr, renders the digest, and advances the project's checkpoint after both sections have been collected successfully.

- Include every article on page one in feed order with its displayed rating, even when it appeared in the previous digest.
- Starting with page two, include only publications since the previous successful pass with a rating of +2 or higher. Stop at the saved boundary. On the first run use the previous 24 hours as the boundary for these pages.
- Include the full list of article cards shown in «Читают сейчас», in sidebar order and regardless of age or rating. If an article appears in both sections, keep it in both.

On success, return the script's Markdown directly in the chat. Keep the two sections and the full title, numeric rating, and clickable link on each line. If the script fails, report the specific issue in Russian. The checkpoint is preserved on failures so the next request can retry the same interval.
