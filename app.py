from flask import Flask, request, jsonify
import os
import secrets

app = Flask(__name__)
temp_storage = {}

@app.route('/create', methods=['POST'])
def create_url():
    text = request.json['text']
    token = secrets.token_urlsafe(16)
    temp_storage[token] = text
    return jsonify({'url': f'/access/{token}'})

@app.route('/access/<token>', methods=['GET'])
def access_text(token):
    if token in temp_storage:
        text = temp_storage.pop(token)
        return text, 200
    return 'Not found or already accessed', 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
