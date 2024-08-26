from flask import Flask, request, jsonify
import os
import secrets
import time
from collections import defaultdict

app = Flask(__name__)
temp_storage = {}
request_counts = defaultdict(list)

def clean_old_entries():
    current_time = time.time()
    for token in list(temp_storage.keys()):
        if current_time - temp_storage[token]['timestamp'] > 60:  # 60 segundos = 1 minuto
            del temp_storage[token]

def is_rate_limited(ip):
    current_time = time.time()
    request_counts[ip] = [t for t in request_counts[ip] if current_time - t < 60]
    if len(request_counts[ip]) >= 3:
        return True
    request_counts[ip].append(current_time)
    return False

@app.route('/create', methods=['POST'])
def create_url():
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    
    if is_rate_limited(client_ip):
        return jsonify({'error': 'Rate limit exceeded'}), 429

    clean_old_entries()

    text = request.json['text']
    token = secrets.token_urlsafe(16)
    temp_storage[token] = {
        'text': text,
        'timestamp': time.time()
    }
    return jsonify({'url': f'/access/{token}'})

@app.route('/access/<token>', methods=['GET'])
def access_text(token):
    clean_old_entries()
    if token in temp_storage:
        text = temp_storage.pop(token)['text']
        return text, 200
    return 'Not found or already accessed', 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
