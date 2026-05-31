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
  name already existed). Pushing commits and **creating branches/refs**
  (`Contents: write`) works.
- **Has repo-scoped `Administration: write`** on `hzmchen/research` — verified by a
  no-op `PATCH /repos/hzmchen/research` (→ 200). So it **can** change repo settings
  (incl. `default_branch`) and set **branch protection** on this repo. The
  `permissions` object for the repo reports `admin: true`.
- **No org-level administration:** managing the org itself (e.g.
  `GET /user/memberships/orgs/hzmchen`) → 403. Repo-level admin only.
- **Cannot create pull requests** (`POST /repos/.../pulls` → `Resource not
  accessible by personal access token`). The token lacks **Pull requests: Read &
  write** (PR *reads* return 200, but creates are blocked). Until that permission
  is granted, open PRs via the **web UI** (see Workflow below).

### Required token permissions

Fine-grained PAT permissions, mapped to what each unlocks. The current token
covers only the first two rows; the rest need to be granted to remove the manual
workarounds noted above.

| Permission | Level | Enables |
| ---------- | ----- | ------- |
| **Metadata** | Read | Mandatory baseline for any repo access (always required). |
| **Contents** | Read & write | Clone, push commits, create/update branches, refs, tags. ✅ have |
| **Pull requests** | Read & write | Create/update PRs, set assignees & reviewers via API. ❌ missing → PRs must be opened in the web UI |
| **Administration** | Read & write | Manage repo settings (`default_branch`), **branch protection**, and org-repo creation. ✅ have at the **repo** level (org-repo creation + settings + protection work). ❌ does **not** extend to org-level management or personal-account repo creation. |
| **Issues** | Read & write | Manage issues; needed if a workflow files issues (PR assignees go through the issues endpoint but are covered by Pull requests: write). |

So today the only blocker for the full agent workflow is **Pull requests: write** —
everything else (push, branches, repo settings, branch protection) is available.

Scope the token to the **`hzmchen/research`** repository (or the org) rather than
"all repositories" where possible. After changing permissions, the token value is
unchanged but the new grants take effect immediately.

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

## Research tasks — scope & approach

This repo collects research topics. The following conventions apply to **any**
research task, independent of subject.

### Scope

A "research topic" here is open-ended — it may be a survey of data sources, but
equally a comparison of tools or methods, a literature/landscape review, an
evaluation of options against a decision, a feasibility study, a how-things-work
explainer, or anything else worth investigating. The approach below is shape- and
subject-independent.

- **One topic = one subdirectory** (kebab-case name describing the topic).
- **Frame the question first.** State what the topic is trying to answer and the
  boundaries of the investigation, so breadth and depth can be judged against it.
- Be **comprehensive within those boundaries**: identify the relevant dimensions
  (categories, options, perspectives, time periods, stakeholders, …) and cover
  each. Where a spectrum exists, span its full range rather than the obvious end
  — and note what was deliberately left out of scope.
- **Compare on consistent criteria.** When weighing multiple items (sources,
  tools, approaches, options…), pick a small fixed set of evaluation axes
  appropriate to the topic, define them once in the topic's index, and apply them
  uniformly — ideally with a simple rating scale (e.g. ★/★★/★★★) so items are
  directly comparable.
- **Ground claims in evidence** and distinguish fact from inference. Note
  confidence and flag what should be independently verified.
- Be **targeted, not padded**: comprehensive where it matters, with key insights
  surfaced — don't bury conclusions in prose.

### Structure & writing

- Write in **Markdown**, one file per major section, plus an index `README.md`
  that states the topic, method, rating scheme, and a table of contents.
- Every section gets a short **executive summary** at the top and a **key
  insight** callout; finish the whole topic with **one overall executive
  summary** (typically in a final `NN-summary.md`).
- Include **visuals where they help** — comparison tables, Mermaid diagrams,
  ASCII matrices/heatmaps. Use GitHub-compatible syntax (e.g. `<br/>` in Mermaid
  labels).
- End each section with a linked **Sources** list. Cite as you go.
- Mark agent-generated content with a disclaimer banner at the top of each file:
  `> 🤖 Generated by a coding agent — not human-verified.` Flag figures that
  should be re-verified before operational use.

### Branch setup (minimum: `main` + `dev`)

Keep at least two long-lived branches:

- **`main`** — stable, reviewed mainline; the PR target. Treat as protected — the
  token **has** `Administration: write` on this repo, so branch protection can be
  enabled programmatically (`PUT /repos/hzmchen/research/branches/main/protection`).
- **`dev`** — integration/working branch where research lands first.

A repo created empty has **no branches** until the first push, and the **first
branch pushed becomes the default** (that is how this repo ended up defaulting to
`dev`). When bootstrapping a new repo, establish both branches up front and set
`main` as default:

```bash
# from an empty clone
git checkout -b main
git commit --allow-empty -m "chore: initialize main"
git push -u origin main
git checkout -b dev
git push -u origin dev
```

Then set `main` as the default branch — the token has `Administration: write`, so
this works via the API (or web UI → Settings → Branches):

```bash
curl -s -X PATCH -H "Authorization: token ${GH_HZM_TOKEN}" \
  -H "Accept: application/vnd.github+json" \
  https://api.github.com/repos/hzmchen/research \
  -d '{"default_branch":"main"}'
```

(For this repo, hold off on switching the default to `main` until `dev` is merged,
so the default branch doesn't show stale content.) If only `dev` exists on an
existing repo, create `main` from the root commit so a PR base exists:

```bash
ROOT=$(git rev-list --max-parents=0 HEAD)
curl -s -X POST -H "Authorization: token ${GH_HZM_TOKEN}" \
  -H "Accept: application/vnd.github+json" \
  https://api.github.com/repos/hzmchen/research/git/refs \
  -d "{\"ref\":\"refs/heads/main\",\"sha\":\"${ROOT}\"}"
```

### Workflow

- Work on the **`dev`** branch (or a topic branch off it) — never commit
  straight to `main`.
- Make **atomic commits** (one logical unit each, e.g. one section) and
  **push to `dev` as you go**, so progress is visible and recoverable.
- When the task is done, **open a merge request / pull request** targeting
  `main` summarizing the topic and what was produced.
- ⚠️ Neither the `gh` CLI **nor** the REST API works for this with the current
  token (it lacks `Pull requests: write` — see the token section above). **Open
  the PR through the web UI** using a compare link, then add assignees/reviewers
  in the sidebar:

  ```
  https://github.com/hzmchen/research/compare/main...dev?expand=1
  ```

  If the token is later granted `Pull requests: Read & write`, a PR can be created
  programmatically instead:

  ```bash
  curl -s -X POST \
    -H "Authorization: token ${GH_HZM_TOKEN}" \
    -H "Accept: application/vnd.github+json" \
    https://api.github.com/repos/hzmchen/research/pulls \
    -d '{"title":"research: <topic>","head":"dev","base":"main","body":"<summary of scope, method, and key findings>"}'
  # then assign: POST /repos/hzmchen/research/issues/<pr_number>/assignees {"assignees":["nielsaka"]}
  ```
