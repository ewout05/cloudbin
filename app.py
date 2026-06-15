from flask import Flask, request, jsonify, abort, render_template, redirect
import uuid
from datetime import timedelta
from google.cloud import storage
import google.auth
from google.auth.transport import requests as google_auth_requests

app = Flask(__name__)

BUCKET_NAME = "haste_ewout05_com"
# The content-type we sign must exactly match what the browser sends on the PUT,
# otherwise GCS rejects the signed URL (SignatureDoesNotMatch).
UPLOAD_CONTENT_TYPE = "text/plain; charset=utf-8"

# On Cloud Run, storage.Client() automatically uses the credentials of the attached
# service account (Application Default Credentials). No key file needed.
client = storage.Client()


def _generate_upload_url(snippet_id):
    # v4 signed URL so the browser PUTs straight to GCS (bypassing Cloud Run).
    # Signing is keyless, via the IAM Credentials API (signBlob) using the SA itself.
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

# POST /upload-url - Request a signed URL to upload directly to GCS.
# The client sends no content here; it only gets a URL back and then PUTs the
# bytes itself to Google Cloud Storage (bypassing Cloud Run).
@app.route('/upload-url', methods=['POST'])
def create_upload_url():
    snippet_id = str(uuid.uuid4())[:8]  # Unique 8-character ID
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

# GET /r/<snippet_id> - Fetch a snippet
@app.route('/r/<snippet_id>.<language>', methods=['GET'])
@app.route('/r/<snippet_id>', methods=['GET'])
def get_snippet(snippet_id, language="(auto)"):
    # Fetch the snippet from Google Cloud Storage
    blob = client.bucket(BUCKET_NAME).blob(snippet_id)
    if snippet_id == "about":
        language = "md"
        with open('about.md', 'r') as file:
            content = file.read()
    else:
        try:
            # Try to fetch the blob's contents
            content = blob.download_as_text()
        except Exception as e:
            # return jsonify({'error': f'Snippet not found: {str(e)}'}), 404
            # return # redirect to /r/about.md
            return redirect("/")

    # Render the content in the template (or return raw text if you prefer)
    disabled = {"savepaste": True, "new_paste": False, "duplicate_edit": False, "raw_text": False}
    return render_template('index.html', language=language, code=content, new_paste=False, snippet_id=snippet_id, disabled=disabled)



# GET /raw/<snippet_id> - Raw version of a snippet
@app.route('/raw/<snippet_id>.<language>', methods=['GET'])
@app.route('/raw/<snippet_id>', methods=['GET'])
def get_raw_snippet(snippet_id, language=None):
    # Fetch the snippet from Google Cloud Storage
    blob = client.bucket(BUCKET_NAME).blob(snippet_id)
    if snippet_id == "about":
        language = "md"
        with open('about.md', 'r') as file:
            content = file.read()
    else:
        try:
            # Try to fetch the blob's contents
            content = blob.download_as_text()
        except Exception as e:
            # return jsonify({'error': f'Snippet not found: {str(e)}'}), 404
            return jsonify({'error': f'Snippet not found'}), 404

    # Render the content in the template (or return raw text if you prefer)
    return f"<pre>{content}</pre>"  # Or return raw text if you prefer: content

# Run the app
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=False)