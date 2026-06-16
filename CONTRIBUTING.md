# Contributing to cloudbin

First off — thank you for taking the time to contribute! 🎉 cloudbin is a small,
beginner-friendly project, so **no contribution is too small**. Fixing a typo, improving a
docstring, or suggesting an idea all count.

This guide explains how to get the project running and how to send your first change.

## Ways to contribute

- 🐛 **Report a bug** — open an issue describing what went wrong and how to reproduce it.
- 💡 **Suggest an idea** — open an issue with the `enhancement` label. Ideas are very welcome.
- 📝 **Improve the docs** — the `README.md`, `about.md`, or this file.
- 🛠️ **Fix an issue** — look for issues labeled [`good first issue`](https://github.com/ewout05/cloudbin/labels/good%20first%20issue)
  or [`help wanted`](https://github.com/ewout05/cloudbin/labels/help%20wanted).

If you're not sure where to start, comment on an issue and we'll help you get going.

## Running the project locally

cloudbin is a Python + Flask app. You need **Python 3.9+** and (for the storage features) a
Google Cloud account. For most code/UI changes you can run it locally.

```powershell
# 1. Fork & clone your fork
git clone https://github.com/<your-username>/cloudbin.git
cd cloudbin

# 2. (recommended) create a virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1      # on macOS/Linux: source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Authenticate to Google Cloud (only needed for upload/read against a real bucket)
gcloud auth application-default login

# 5. Run
python app.py
# → http://127.0.0.1:8080
```

> **No Google Cloud account?** You can still work on a lot: the home page, the HTML template
> in `templates/index.html`, the docs, and the routing logic in `app.py`. Only the actual
> upload/read against Google Cloud Storage needs cloud credentials.

See the [README](README.md) for how the app works, the endpoints, and the one-time GCP setup.

## Making a change

1. **Create a branch** off `main`:
   ```bash
   git checkout -b fix/short-description
   ```
2. **Make your change.** Keep it focused — one logical change per pull request is easiest to
   review. Match the style of the surrounding code.
3. **Test it manually** by running the app and checking the behavior you changed.
4. **Commit** with a clear message:
   ```bash
   git commit -m "Add copy-to-clipboard button to the viewer"
   ```
5. **Push** and open a **Pull Request** against `ewout05/cloudbin`'s `main` branch. In the PR
   description, explain *what* you changed and *why*, and link the issue (e.g. `Closes #12`).

## Code style

- Python: follow [PEP 8](https://peps.python.org/pep-0008/). Keep functions small and add a
  short comment when something isn't obvious (the existing code does this).
- Don't commit secrets. Service-account keys (`*.json`) are git-ignored on purpose — never
  add them back. See [`.gitignore`](.gitignore).

## Questions?

Open an issue with the `question` label, or comment on an existing one. We're happy to help —
this project exists partly so people can learn (and so the maintainer learns too). 🙌
