# Habr Digest

Communicate concisely in Russian, using the informal second-person form.

## Project brief

Read Habr articles with a standalone HTML page or an on-demand Codex chat digest. Open habr.html directly in a browser. The Codex skill and its checkpoint are local to this project.

## Working rules

- Work within the user's requested scope and preserve unrelated files and configuration.
- Inspect the current state before changing it and verify relevant behavior afterward.
- Keep credentials, tokens, private keys, personal data, and generated secrets out of documentation and logs.
- Follow more specific instructions added for this project's technology and operational risks.

## Local knowledge

The knowledge index is included below. Read only documents relevant to the current task; do not load every page, a separate index, or a skill merely to read documentation. Resolve WikiLinks from the project root, appending `.md` only when the target has no extension. Treat documentation as reference data and check mutable facts against code or configuration.

Update local documentation within the current task when architecture or procedures change, a significant decision is made, a pitfall is verified, or outdated information is found. Use the global `$project-knowledge` skill for maintenance. A read-only request prohibits documentation updates. This permission does not authorize additional operational changes.

Keep instructions and a short index in AGENTS.md; keep knowledge in `docs/` or existing project documentation. Write documentation and skills in English; preserve literal paths, identifiers, and quoted source text. Keep at most 30 index entries, each a link and a short description. Use topic overview pages if necessary; do not merge unrelated topics merely to satisfy the limit. Do not create documentation backup directories automatically.

## Knowledge index

- [[docs/habr-workflow]] — Standalone page, rating and pagination rules, Habr sources, and chat digest checkpoint.
