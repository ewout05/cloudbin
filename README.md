# cloudbin

A scalable [hastebin](https://github.com/toptal/haste-server)-style pastebin built with
**Python + Flask**, storing snippets in **Google Cloud Storage** and running serverless on
**Google Cloud Run**.

Paste text, get a short URL, share it. Because storage is GCS and compute is Cloud Run, it
scales from zero to as much traffic as you throw at it without managing any servers.

> Looking for the user-facing docs (CLI usage, paste lifetime, etc.)? Those live in
> [`about.md`](about.md) and are served inside the app at `/r/about`.

## How it works

```
                  ┌──────────────┐     upload_from_string()   ┌─────────────────────┐
  POST /create ──▶│  Flask app   │ ─────────────────────────▶ │  GCS bucket         │
  GET  /r/<id> ◀──│  (app.py)    │ ◀───────────────────────── │  haste_ewout05_com  │
                  └──────────────┘     download_as_text()      └─────────────────────┘
                   on Cloud Run
```

1. A snippet is created via `POST /create`. The server generates a random 8-character ID
   (`uuid4()[:8]`) and writes the content to an object with that name in the GCS bucket.
2. Reading a snippet (`GET /r/<id>`) downloads the object from the bucket and renders it in
   the HTML template. Unknown IDs redirect back to the home page.
3. There is no database — each paste is simply one object in the bucket, which is what makes
   it horizontally scalable.

### Authentication

On Cloud Run the app uses **Application Default Credentials (ADC)**: `storage.Client()`
automatically picks up the credentials of the service account attached to the Cloud Run
service. No service-account key file is needed (and none should ever be committed — see
[`.gitignore`](.gitignore)).

For **local** development, authenticate once with:

```powershell
gcloud auth application-default login
```

## Endpoints

| Method | Path                      | Description                                                        |
| ------ | ------------------------- | ------------------------------------------------------------------ |
| `GET`  | `/`                       | Home page with the editor to create a new paste.                   |
| `POST` | `/create`                 | Create a paste. JSON body `{"content": "..."}`. Returns the `id`.  |
| `GET`  | `/r/<id>`                 | View a paste rendered in the web UI (optionally `/r/<id>.<lang>`). |
| `GET`  | `/raw/<id>`               | View the raw paste content (optionally `/raw/<id>.<lang>`).        |
| `GET`  | `/r/about`                | Render `about.md` (the project's about page).                      |

### Create a paste

```bash
curl -X POST https://hastebin-433793328025.europe-west1.run.app/create \
  -H "Content-Type: application/json" \
  -d '{"content": "hello world"}'
# {"id": "a1b2c3d4", "language": "(auto)", "message": "Snippet created successfully"}
```

Then open `https://.../r/a1b2c3d4` to view it.

## Project structure

```
cloudbin/
├── app.py             # Flask app: routes + GCS read/write
├── templates/
│   └── index.html     # Web UI (editor + viewer)
├── about.md           # User-facing about page, served at /r/about
├── Dockerfile         # Container image (gunicorn on port 8080)
├── requirements.txt   # Python dependencies
├── .gitignore         # Ignores secrets (*.json keys) and Python artifacts
└── .dockerignore      # Keeps secrets out of the built image
```

## Running locally

```powershell
# 1. Install dependencies
pip install -r requirements.txt

# 2. Authenticate to Google Cloud (once)
gcloud auth application-default login

# 3. Run
python app.py
# → http://127.0.0.1:8080
```

Or run it exactly like production, in a container:

```powershell
docker build -t cloudbin .
docker run -p 8080:8080 cloudbin
```

## Deploying to Cloud Run

### Option A — Manual deploy

```powershell
gcloud run deploy hastebin --source . --region europe-west1
```

This builds the image from the `Dockerfile` and deploys a new revision.

### Option B — Continuous deployment from GitHub (recommended)

Connect the repo so every `git push` to `main` is automatically built and deployed:

1. In the Cloud Run service, click **Connect to repo** / **Set up with Cloud Build**.
2. Install the **Google Cloud Build** GitHub App on this repository.
3. Pick the branch (`^main$`) and **Dockerfile** as the build type.

From then on: **push to `main` → build → live**, no manual commands needed.

## Configuration

The bucket name is currently hard-coded in `app.py` as `haste_ewout05_com`. Change it there
if you deploy against a different bucket.

## Tech stack

- **Python 3.9** + **Flask** (web framework)
- **Gunicorn** (WSGI server in production)
- **Google Cloud Storage** (snippet storage)
- **Google Cloud Run** (serverless container hosting)
- **Cloud Build** (CI/CD from GitHub)

## Credits

Inspired by the original [haste-server](https://github.com/toptal/haste-server) by John
Crepezzi. See [`about.md`](about.md) for more.
