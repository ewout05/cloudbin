# cloudbin

A scalable [hastebin](https://github.com/toptal/haste-server)-style pastebin built with
**Python + Flask**, storing snippets in **Google Cloud Storage** and running serverless on
**Google Cloud Run**.

Paste text, get a short URL, share it. Because storage is GCS and compute is Cloud Run, it
scales from zero to as much traffic as you throw at it without managing any servers.

> Looking for the user-facing docs (CLI usage, paste lifetime, etc.)? Those live in
> [`about.md`](about.md) and are served inside the app at `/r/about`.

## How it works

Uploads use **GCS v4 signed URLs** so the paste content goes *directly* from the browser to
Cloud Storage and never passes through Cloud Run. That matters for cost: if someone uploads
100 GB, you only pay for storage — not for Cloud Run CPU/egress moving those bytes.

```
   1. POST /upload-url   ┌──────────────┐
  ───────────────────────▶│  Flask app   │   asks IAM API to sign a URL (no bytes)
   { id, upload_url }   ◀─│  (app.py)    │
                          └──────────────┘
                           on Cloud Run
   2. PUT <content>       ┌─────────────────────┐
  ────────────────────────▶│  GCS bucket         │   bytes go straight to storage,
     (direct to GCS)       │  haste_ewout05_com  │   bypassing Cloud Run entirely
                           └─────────────────────┘
   3. GET /r/<id>  ── Cloud Run reads the object and renders it in the web UI
```

1. The browser calls `POST /upload-url`. The server generates a random 8-character ID
   (`uuid4()[:8]`) and returns a short-lived (15 min) signed URL that grants a single `PUT`.
2. The browser `PUT`s the content **directly to GCS** using that URL. The bytes never touch
   Cloud Run.
3. Reading a snippet (`GET /r/<id>`) downloads the object and renders it in the HTML
   template. Unknown IDs redirect back to the home page. *(Reads still go through Cloud Run;
   only uploads are offloaded.)*
4. There is no database — each paste is simply one object in the bucket, which is what makes
   it horizontally scalable.

### Signing without a key file

On Cloud Run there is no local private key (we rely on ADC). Signing the URL therefore uses
the **IAM Service Account Credentials API** (`signBlob`) with the runtime service account
itself. See the [one-time GCP setup](#one-time-gcp-setup-for-signed-urls) below.

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

| Method | Path          | Description                                                                       |
| ------ | ------------- | --------------------------------------------------------------------------------- |
| `GET`  | `/`           | Home page with the editor to create a new paste.                                  |
| `POST` | `/upload-url` | Returns `{id, upload_url, content_type}` — a signed URL to `PUT` the content to.  |
| `GET`  | `/r/<id>`     | View a paste rendered in the web UI (optionally `/r/<id>.<lang>`).                |
| `GET`  | `/raw/<id>`   | View the raw paste content (optionally `/raw/<id>.<lang>`).                       |
| `GET`  | `/r/about`    | Render `about.md` (the project's about page).                                     |

### Create a paste

Creating a paste is a two-step flow (the bytes go straight to GCS):

```bash
BASE=https://hastebin-433793328025.europe-west1.run.app

# 1. Ask for a signed upload URL
RESP=$(curl -s -X POST "$BASE/upload-url")
ID=$(echo "$RESP" | jq -r .id)
URL=$(echo "$RESP" | jq -r .upload_url)

# 2. PUT the content directly to Cloud Storage
curl -X PUT "$URL" -H "Content-Type: text/plain; charset=utf-8" -d "hello world"

echo "$BASE/r/$ID"   # open this to view the paste
```

The `Content-Type` of the `PUT` must exactly match the `content_type` returned in step 1,
otherwise GCS rejects the signature.

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

## One-time GCP setup for signed URLs

Because the app signs URLs with the runtime service account (no key file), three things must
be configured once. Run these with an account that has owner/admin rights:

```powershell
# 1. Enable the IAM Service Account Credentials API (used to sign without a key)
gcloud services enable iamcredentials.googleapis.com --project ewout05-apis

# 2. Let the Cloud Run service account sign on its own behalf (signBlob)
gcloud iam service-accounts add-iam-policy-binding `
  433793328025-compute@developer.gserviceaccount.com `
  --member="serviceAccount:433793328025-compute@developer.gserviceaccount.com" `
  --role="roles/iam.serviceAccountTokenCreator" `
  --project ewout05-apis

# 3. Allow the browser to PUT directly to the bucket (CORS) — see cors.json
gsutil cors set cors.json gs://haste_ewout05_com
```

If `/upload-url` returns a 500 with a `signBlob`/permission error, step 1 or 2 is missing.
If the browser shows a CORS error on the `PUT`, step 3 is missing or the origin in
[`cors.json`](cors.json) doesn't match your Cloud Run URL.

## Configuration

The bucket name is currently hard-coded in `app.py` as `haste_ewout05_com`. Change it there
if you deploy against a different bucket. If you change it, also update the bucket in the
`gsutil cors set` command above.

## Tech stack

- **Python 3.9** + **Flask** (web framework)
- **Gunicorn** (WSGI server in production)
- **Google Cloud Storage** (snippet storage)
- **Google Cloud Run** (serverless container hosting)
- **Cloud Build** (CI/CD from GitHub)

## Credits

Inspired by the original [haste-server](https://github.com/toptal/haste-server) by John
Crepezzi. See [`about.md`](about.md) for more.
