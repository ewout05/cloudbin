from re import template
from flask import Flask, request, jsonify, abort, render_template, redirect
import uuid
from google.cloud import storage

app = Flask(__name__)

# Tijdelijke opslag voor snippets
data_storage = {}
# Op Cloud Run gebruikt storage.Client() automatisch de credentials van de
# gekoppelde service account (Application Default Credentials). Geen key-bestand nodig.
client = storage.Client()

# POST /create - Nieuwe snippet maken
@app.route('/create', methods=['POST'])
def create_snippet():
    request_data = request.get_json()
    if not request_data or 'content' not in request_data or not request_data['content'] or request_data['content'] == '':
        return jsonify({'error': 'Content is required'}), 400

    content = request_data['content']
    language = detect_programming_language(content)
    snippet_id = str(uuid.uuid4())[:8]  # Unieke ID van 8 karakters

    # Opslag van de snippet
    # data_storage[snippet_id] = content

    # Opslag in Google Cloud Storage
    bucket = client.get_bucket('haste_ewout05_com')
    blob = bucket.blob(snippet_id)
    blob.upload_from_string(content)
    return jsonify({'id': snippet_id, "language": language, 'message': 'Snippet created successfully'}), 201



def detect_programming_language(content):
    result = "(auto)"
    return result

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
    bucket = client.get_bucket('haste_ewout05_com')  # Zorg ervoor dat je de juiste bucketnaam hebt
    blob = bucket.blob(snippet_id)
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
    bucket = client.get_bucket('haste_ewout05_com')  # Zorg ervoor dat je de juiste bucketnaam hebt
    blob = bucket.blob(snippet_id)
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