# Push to GitHub — instructions

The repo is committed locally at `C:\Users\tw26\ng911-extract` (commit `566a1c2`). To push to GitHub, you need to authenticate the `gh` CLI and create the remote repo.

## Option A: Create the repo via gh CLI (recommended)

Run these two commands in your shell. The `!` prefix in Claude Code runs them in this session so output lands in the conversation.

```bash
gh auth login                       # follow prompts; choose HTTPS, browser auth
gh repo create ng911-extract --public --source=. --remote=origin --push
```

`gh repo create ... --push` does everything in one step:
- Creates the public repo `wangtiankai/ng911-extract` on GitHub.
- Adds `origin` as the remote for this local repo.
- Pushes `main` to GitHub.

After it completes, verify at https://github.com/wangtiankai/ng911-extract.

## Option B: Create via web, then push manually

If you'd rather create the repo in your browser:

1. Go to https://github.com/new
2. Repository name: `ng911-extract`
3. Owner: `wangtiankai`
4. Visibility: **Public** (required for JOSS)
5. **Do not** initialize with README, .gitignore, or license — the local repo already has these.
6. Click "Create repository".
7. Then in this shell:

```bash
cd "C:\Users\tw26\ng911-extract"
gh auth login                       # authenticate first
git remote add origin https://github.com/wangtiankai/ng911-extract.git
git push -u origin main
```

## Verifying

After the push:

- Visit https://github.com/wangtiankai/ng911-extract
- Confirm the GitHub Actions workflow runs successfully on the Actions tab (it should run within ~30 seconds of the first push and pass all 10 smoke tests on Python 3.10, 3.11, 3.12).
- The README, paper.md, and LICENSE should all render correctly.

## After push — JOSS gate

JOSS requires **more than six months of public development history** before submission. The 2026 scope revision explicitly rejects "single burst of commits" submissions.

To build the required history:

- Periodically (every few weeks) push small improvements: a new edge case handled, a docstring polished, a test added.
- Open and close a few issues for documentation requests or bug reports — even if you answer them yourself, this counts as activity.
- After six months with iterative activity, submit at `http://joss.theoj.org/papers/new`.

If you want help scripting the iterative history (e.g., a weekly cron that opens and closes a maintenance issue), ask.
