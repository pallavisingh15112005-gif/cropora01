# Working agreement — cropora01

## Remote

Yeh folder `cropora01` project hai aur iska remote hai:

- `origin` -> https://github.com/pallavisingh15112005-gif/cropora01.git
- Branch: `main` (local `main` tracks `origin/main`)

## Commit aur push

- Har meaningful change ke baad commit karo — kaam sirf local mat chhodo.
- Commit ke baad hamesha push karo:

```bash
git add -A
git commit -m "feat: <kya badla>"
git push origin main
```

- Subject Conventional Commit style me rakho: `feat:`, `fix:`, `docs:`,
  `refactor:`, `chore:`.
- Commit chhote aur focused rakho; unrelated changes ek commit me na milao.

## Secrets aur data

- API keys, tokens, `.streamlit/secrets.toml` kabhi commit mat karo.
- Bade local/derived data files (`.db`, caches) gitignore me rakho.
- Sample dataset (`mandi_prices.csv`) repo me rehta hai taaki app bina network
  ke chale.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate      # Windows
pip install -r requirements.txt
```
