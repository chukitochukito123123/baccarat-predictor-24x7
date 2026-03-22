import os
import re
import time
import json
import random
import requests
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
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

STATIC_DIST = os.path.join(os.path.dirname(__file__), 'staticdist')

class BaccaratPredictor:
    def __init__(self):
        self.history = []
        self.stats = {
            'banker': 0, 'player': 0, 'tie': 0,
            'banker_streak': 0, 'player_streak': 0,
            'martingala_level': 1
        }
        self.model = self._train_model()
        self.last_scrape = None
        
    def _train_model(self):
        X, y = [], []
        patterns = [
            ([1,1,1,0,1], 1), ([0,0,0,1,0], 0), ([1,0,1,0,1], 1),
            ([0,1,0,1,0], 0), ([1,1,0,1,1], 1), ([0,0,1,0,0], 0)
        ] * 1000
        random.shuffle(patterns)
        
        for pattern, outcome in patterns:
            X.append(pattern)
            y.append(outcome)
            
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X, y)
        return model
    
    def scrape_bc_game(self):
        try:
            url = "https://bc.game/casino/baccarat"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, 'lxml')
            
            history_elements = soup.find_all('div', class_=re.compile(r'history|result|round'))
            recent_results = []
            
            for elem in history_elements[-10:]:
                text = elem.get_text().strip().lower()
                if 'banker' in text or 'b' in text:
                    recent_results.append(1)
                elif 'player' in text or 'p' in text:
                    recent_results.append(0)
                elif 'tie' in text:
                    recent_results.append(2)
            
            if len(recent_results) >= 5:
                self.history = recent_results[-20:]
                self._update_stats()
                self.last_scrape = datetime.now()
                logger.info(f"🚀 Scraped {len(recent_results)} results from BC.Game")
                return True
        except Exception as e:
            logger.error(f"Scrape failed: {e}")
        return False
    
    def predict_ml(self):
        if len(self.history) < 5:
            return {'prediction': 'Banker', 'confidence': 0.6, 'martingala': 1}
        
        recent = np.array(self.history[-5:]).reshape(1, -1)
        prob = self.model.predict_proba(recent)[0]
        prediction = 1 if prob[1] > prob[0] else 0
        
        confidence = max(prob)
        result = 'Banker' if prediction == 1 else 'Player'
        streak = self.stats['banker_streak'] if prediction == 1 else self.stats['player_streak']
        martingala = min(7, streak + 1)
        
        return {
            'prediction': result,
            'confidence': float(confidence),
            'martingala': martingala,
            'strategy': f"Martingala Level {martingala}x"
        }
    
    def add_result(self, result):
        if result == 'Banker':
            self.history.append(1)
            self.stats['banker'] += 1
            self.stats['banker_streak'] += 1
            self.stats['player_streak'] = 0
        elif result == 'Player':
            self.history.append(0)
            self.stats['player'] += 1
            self.stats['player_streak'] += 1
            self.stats['banker_streak'] = 0
        else:
            self.history.append(2)
            self.stats['tie'] += 1
            self.stats['banker_streak'] = 0
            self.stats['player_streak'] = 0
        
        self.history = self.history[-50:]
        self._update_stats()
    
    def _update_stats(self):
        total = len(self.history)
        if total > 0:
            self.stats['banker_pct'] = (self.stats['banker'] / total) * 100
            self.stats['player_pct'] = (self.stats['player'] / total) * 100

predictor = BaccaratPredictor()

@app.route('/')
def serve_index():
    if os.path.exists(os.path.join(STATIC_DIST, 'index.html')):
        return send_from_directory(STATIC_DIST, 'index.html')
    return "Static files not found. Build frontend first.", 404

@app.route('/assets/<path:filename>')
def serve_assets(filename):
    return send_from_directory(STATIC_DIST, filename)

@app.route('/api/predict')
def predict():
    predictor.scrape_bc_game()
    time.sleep(0.5)
    prediction = predictor.predict_ml()
    return jsonify(prediction)

@app.route('/api/history')
def get_history():
    history = []
    for result in predictor.history[-20:]:
        if result == 1:
            history.append({'result': 'Banker', 'color': 'red'})
        elif result == 0:
            history.append({'result': 'Player', 'color': 'blue'})
        else:
            history.append({'result': 'Tie', 'color': 'green'})
    return jsonify(history)

@app.route('/api/stats')
def get_stats():
    return jsonify(predictor.stats)

@app.route('/api/add_result', methods=['POST'])
def add_result():
    data = request.json
    result = data.get('result')
    if result in ['Banker', 'Player', 'Tie']:
        predictor.add_result(result)
        return jsonify({'success': True})
    return jsonify({'error': 'Invalid result'}), 400

def scraper_loop():
    """Simple scraper every 30s"""
    def run_scrape():
        predictor.scrape_bc_game()
        Timer(30.0, run_scrape).start()
    
    run_scrape()

if __name__ == '__main__':
    scraper_thread = Thread(target=scraper_loop, daemon=True)
    scraper_thread.start()
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)