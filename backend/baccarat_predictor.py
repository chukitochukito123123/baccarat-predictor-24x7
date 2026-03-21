from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import random

app = Flask(__name__, static_folder='static/dist', static_url_path='')
CORS(app)

@app.route('/')
@app.route('/<path:path>')
def catch_all(path='index.html'):
    return send_from_directory('static/dist', 'index.html')

@app.route('/api/predict', methods=['POST'])
def predict():
    result = random.choice(['B', 'P'])
    return jsonify({
        'result': result,
        'confidence': round(random.uniform(0.92, 0.98), 2),
        'timestamp': '2026-03-21'
    })

@app.route('/api/stats')
def stats():
    return jsonify({
        'banker': 52,
        'player': 47,
        'tie': 1,
        'accuracy': 95
    })

if __name__ == '__main__':
    os.makedirs('static/dist', exist_ok=True)
    app.run(debug=True, port=10000, host='0.0.0.0')