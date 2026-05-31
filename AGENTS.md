# AGENTS.md

Notes for AI agents working in this repository.

## Repository

- **Repo:** `hzmchen/research` — https://github.com/hzmchen/research
- **Owner:** the `hzmchen` GitHub organization (not a personal account).
- **Visibility:** public.

## GitHub authentication

- Auth uses a token in the `GH_HZM_TOKEN` environment variable.
- The token authenticates as the user **`nielsaka`**.
- It is a **fine-grained personal access token** (no `x-oauth-scopes` header is
  returned by the API).

### What the token can and cannot do

- **Cannot** create repositories under the personal account (`POST /user/repos`)
  — returns `Resource not accessible by personal access token`. The token lacks
  the **Administration: Read & write** permission on the personal account.
- **Can** operate on repositories in the `hzmchen` org (e.g. `POST
  /orgs/hzmchen/repos` is accepted; creating `research` only failed because the
  name already existed).

### Cloning / pushing with the token

Embed the token as an `x-access-token` credential in the remote URL:

```bash
git clone "https://x-access-token:${GH_HZM_TOKEN}@github.com/hzmchen/research.git"
```

## Git identity for commits

Use the following author identity when committing as an agent:

```bash
git config user.name  "claudebot"
git config user.email "nielsaka+claudebot@users.noreply.github.com"
```

The email follows GitHub's standard no-reply pattern
(`<user>@users.noreply.github.com`), scoped to `nielsaka` with a `+claudebot`
label.
