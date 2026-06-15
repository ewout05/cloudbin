from flask import Flask, request, jsonify, abort, render_template, redirect
import uuid
from datetime import timedelta
from google.cloud import storage
import google.auth
from google.auth.transport import requests as google_auth_requests

app = Flask(__name__)

BUCKET_NAME = "haste_ewout05_com"
# Content-type die we signen moet exact overeenkomen met wat de browser bij de
# PUT meestuurt, anders weigert GCS de signed URL (SignatureDoesNotMatch).
UPLOAD_CONTENT_TYPE = "text/plain; charset=utf-8"

# Op Cloud Run gebruikt storage.Client() automatisch de credentials van de
# gekoppelde service account (Application Default Credentials). Geen key-bestand nodig.
client = storage.Client()


def _generate_upload_url(snippet_id):
    # v4 signed URL zodat de browser rechtstreeks naar GCS PUT't (buiten Cloud Run om).
    # Tekenen gebeurt keyloos via de IAM Credentials API (signBlob) met de SA zelf.
    credentials, _ = google.auth.default()
    credentials.refresh(google_auth_requests.Request())

    blob = client.bucket(BUCKET_NAME).blob(snippet_id)
    return blob.generate_signed_url(
        version="v4",
        expiration=timedelta(minutes=15),
        method="PUT",
        content_type=UPLOAD_CONTENT_TYPE,
        service_account_email=credentials.service_account_email,
        access_token=credentials.token,
    )

# POST /upload-url - Vraag een signed URL om rechtstreeks naar GCS te uploaden.
# De client genereert geen inhoud hier; hij krijgt enkel een URL terug en PUT't
# de bytes daarna zelf naar Google Cloud Storage (buiten Cloud Run om).
@app.route('/upload-url', methods=['POST'])
def create_upload_url():
    snippet_id = str(uuid.uuid4())[:8]  # Unieke ID van 8 karakters
    upload_url = _generate_upload_url(snippet_id)
    return jsonify({
        'id': snippet_id,
        'upload_url': upload_url,
        'content_type': UPLOAD_CONTENT_TYPE,
    }), 200

# GET / - home page input
@app.route('/', methods=['GET'])
def home():
    disabled = {"savepaste": False, "new_paste": False, "duplicate_edit": True, "raw_text": True}
    return render_template('index.html', new_paste=True, disabled=disabled)

# GET /r/<snippet_id> - Ophalen van een snippet
@app.route('/r/<snippet_id>.<language>', methods=['GET'])
@app.route('/r/<snippet_id>', methods=['GET'])
def get_snippet(snippet_id, language="(auto)"):
    # Ophalen van de snippet van Google Cloud Storage
    blob = client.bucket(BUCKET_NAME).blob(snippet_id)
    if snippet_id == "about":
        language = "md"
        with open('about.md', 'r') as file:
            content = file.read()
    else:
        try:
            # Probeer de inhoud van de blob op te halen
            content = blob.download_as_text()
        except Exception as e:
            # return jsonify({'error': f'Snippet not found: {str(e)}'}), 404
            # return # redirect to /r/about.md
            return redirect("/")

    # Render de inhoud in de template (of je kan raw tekst terugsturen als je wil)
    disabled = {"savepaste": True, "new_paste": False, "duplicate_edit": False, "raw_text": False}
    return render_template('index.html', language=language, code=content, new_paste=False, snippet_id=snippet_id, disabled=disabled)



# GET /raw/<snippet_id> - Raw versie van een snippet
@app.route('/raw/<snippet_id>.<language>', methods=['GET'])
@app.route('/raw/<snippet_id>', methods=['GET'])
def get_raw_snippet(snippet_id, language=None):
    # Ophalen van de snippet van Google Cloud Storage
    blob = client.bucket(BUCKET_NAME).blob(snippet_id)
    if snippet_id == "about":
        language = "md"
        with open('about.md', 'r') as file:
            content = file.read()
    else:
        try:
            # Probeer de inhoud van de blob op te halen
            content = blob.download_as_text()
        except Exception as e:
            # return jsonify({'error': f'Snippet not found: {str(e)}'}), 404
            return jsonify({'error': f'Snippet not found'}), 404

    # Render de inhoud in de template (of je kan raw tekst terugsturen als je wil)
    return f"<pre>{content}</pre>"  # Of je kan raw tekst terugsturen als je wil: content

# Run de app
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=False)