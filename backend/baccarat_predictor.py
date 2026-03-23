import os
import re
import time
import json
import random
import requests
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory, abort
from flask_cors import CORS
from bs4 import BeautifulSoup
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import logging
from threading import Thread, Timer

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ✅ STATIC FILES - usa 'static' folder (crearemos)
STATIC_FOLDER = os.path.join(os.path.dirname(__file__), 'static')
logger.info(f"📁 Serving static from: {STATIC_FOLDER}")

class BaccaratPredictor:
    def __init__(self):
        self.history = []
        self.stats = {'banker': 0, 'player': 0, 'tie': 0, 'banker_streak': 0, 'player_streak': 0}
        self.model = self._train_model()
        
    def _train_model(self):
        X, y = [], []
        patterns = [([1,1,1,0,1], 1), ([0,0,0,1,0], 0), ([1,0,1,0,1], 1), ([0,1,0,1,0], 0)] * 1000
        random.shuffle(patterns)
        for pattern, outcome in patterns: X.append(pattern); y.append(outcome)
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X, y)
        return model
    
    def scrape_bc_game(self):
        try:
            url = "https://bc.game/casino/baccarat"
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, 'lxml')
            history_elements = soup.find_all('div', class_=re.compile(r'history|result|round'))
            recent_results = [1 if 'banker' in e.get_text().lower() else 0 if 'player' in e.get_text().lower() else 2 for e in history_elements[-10:]]
            if len(recent_results) >= 5:
                self.history = recent_results[-20:]
                self._update_stats()
                logger.info("🚀 BC.Game scraped!")
                return True
        except: pass
        return False
    
    def predict_ml(self):
        if len(self.history) < 5: return {'prediction': 'Banker', 'confidence': 0.95, 'martingala': 1}
        recent = np.array(self.history[-5:]).reshape(1, -1)
        prob = self.model.predict_proba(recent)[0]
        pred = 1 if prob[1] > prob[0] else 0
        conf = max(prob)
        result = 'Banker' if pred == 1 else 'Player'
        streak = self.stats['banker_streak'] if pred == 1 else self.stats['player_streak']
        mart = min(7, streak + 1)
        return {'prediction': result, 'confidence': float(conf), 'martingala': mart}
    
    def add_result(self, result):
        if result == 'Banker': self.history.append(1); self.stats['banker']+=1; self.stats['banker_streak']+=1; self.stats['player_streak']=0
        elif result == 'Player': self.history.append(0); self.stats['player']+=1; self.stats['player_streak']+=1; self.stats['banker_streak']=0
        else: self.history.append(2); self.stats['tie']+=1; self.stats['banker_streak']=self.stats['player_streak']=0
        self.history = self.history[-50:]
        self._update_stats()
    
    def _update_stats(self):
        total = len(self.history)
        if total > 0:
            self.stats['banker_pct'] = round((self.stats['banker']/total)*100, 1)
            self.stats['player_pct'] = round((self.stats['player']/total)*100, 1)

predictor = BaccaratPredictor()

@app.route('/')
@app.route('/<path:path>')
def catch_all(path=''):
    """✅ CATCH-ALL: Sirve static + SPA fallback"""
    # APIs first
    if path.startswith('api'): return abort(404)
    
    # Try file, fallback to index.html
    file_path = os.path.join(STATIC_FOLDER, path) if path else os.path.join(STATIC_FOLDER, 'index.html')
    
    if os.path.exists(file_path):
        return send_from_directory(STATIC_FOLDER, os.path.basename(file_path))
    
    # Fallback index.html
    index_path = os.path.join(STATIC_FOLDER, 'index.html')
    if os.path.exists(index_path):
        return send_from_directory(STATIC_FOLDER, 'index.html')
    
    return "Static files not configured", 404

@app.route('/api/predict')
def api_predict():
    predictor.scrape_bc_game()
    return jsonify(predictor.predict_ml())

@app.route('/api/history')
def api_history():
    history = []
    for r in predictor.history[-20:]:
        if r == 1: history.append({'result': 'Banker', 'color': 'bg-red-500'})
        elif r == 0: history.append({'result': 'Player', 'color': 'bg-blue-500'})
        else: history.append({'result': 'Tie', 'color': 'bg-green-500'})
    return jsonify(history)

@app.route('/api/stats')
def api_stats():
    return jsonify(predictor.stats)

@app.route('/api/add_result', methods=['POST'])
def api_add_result():
    data = request.json or {}
    result = data.get('result')
    if result in ['Banker', 'Player', 'Tie']:
        predictor.add_result(result)
        return jsonify({'success': True})
    return jsonify({'error': 'Invalid result'}), 400

def scraper_loop():
    def run(): predictor.scrape_bc_game(); Timer(30, run).start()
    run()

if __name__ == '__main__':
    Thread(target=scraper_loop, daemon=True).start()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)