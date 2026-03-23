import os
import random
import requests
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import logging
from threading import Thread, Timer
from bs4 import BeautifulSoup
import re

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

STATIC_FOLDER = os.path.join(os.path.dirname(__file__), 'static')

# ✅ MEJORAS: Mesas BC.Game + Real-time
BC_GAME_TABLES = {
    'Baccarat 1': 'https://bc.game/casino/baccarat/1',
    'Baccarat 2': 'https://bc.game/casino/baccarat/2', 
    'Baccarat Lobby': 'https://bc.game/casino/baccarat'
}

class BaccaratPredictor:
    def __init__(self):
        self.history = [1,0,1,1,0,2,1,0]  # Seed data
        self.stats = {'banker': 4, 'player': 3, 'tie': 1, 'table': 'Baccarat 1'}
        self.model = self._train_model()
        self.current_table = 'Baccarat 1'
        
    def _train_model(self):
        X, y = [], []
        patterns = [([1,1,1,0,1],1),([0,0,0,1,0],0),([1,0,1,0,1],1)] * 2000
        random.shuffle(patterns)
        for p, o in patterns: X.append(p); y.append(o)
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X, y)
        return model
    
    def scrape_bc_game(self, table='Baccarat 1'):
        try:
            url = BC_GAME_TABLES.get(table, BC_GAME_TABLES['Baccarat Lobby'])
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get(url, headers=headers, timeout=15)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Busca resultados recientes (mejor selector)
            results = soup.find_all('div', class_=re.compile(r'result|history|shoe|road'))
            recent = []
            for r in results[-15:]:
                text = r.get_text().lower()
                if 'banker' in text or 'b' in text: recent.append(1)
                elif 'player' in text or 'p' in text: recent.append(0)
                elif 'tie' in text: recent.append(2)
            
            if len(recent) >= 6:
                self.history = recent[-20:]
                self.stats['table'] = table
                self._update_stats()
                logger.info(f"🚀 {table}: {len(recent)} results scraped")
                return True
        except Exception as e:
            logger.error(f"Scrape {table}: {e}")
        return False
    
    def predict_next(self):
        if len(self.history) < 5:
            return {'prediction': 'Banker', 'confidence': 0.97, 'martingala': 1, 'table': self.stats['table']}
        
        recent = np.array(self.history[-5:]).reshape(1, -1)
        prob = self.model.predict_proba(recent)[0]
        pred = 1 if prob[1] > 0.5 else 0
        conf = max(prob)
        
        result = 'BANKER' if pred == 1 else 'PLAYER'
        streak = self.stats['banker_streak'] if pred == 1 else self.stats['player_streak']
        mart = min(7, streak + 1)
        
        return {
            'prediction': result,
            'confidence': round(float(conf), 3),
            'martingala': mart,
            'table': self.stats['table'],
            'signal': f"🔔 {result} x{mart} en {self.stats['table']}",
            'timestamp': datetime.now().isoformat()
        }
    
    def add_result(self, result):
        num = 1 if result == 'BANKER' else 0 if result == 'PLAYER' else 2
        self.history.append(num)
        if result == 'BANKER': 
            self.stats['banker'] += 1; self.stats['banker_streak'] += 1; self.stats['player_streak'] = 0
        elif result == 'PLAYER': 
            self.stats['player'] += 1; self.stats['player_streak'] += 1; self.stats['banker_streak'] = 0
        else: 
            self.stats['tie'] += 1; self.stats['banker_streak'] = self.stats['player_streak'] = 0
        self.history = self.history[-50:]
        self._update_stats()
    
    def _update_stats(self):
        total = len(self.history)
        self.stats['banker_pct'] = round(self.stats['banker'] / total * 100, 1)
        self.stats['player_pct'] = round(self.stats['player'] / total * 100, 1)

predictor = BaccaratPredictor()

@app.route('/')
@app.route('/<path:path>')
def catch_all(path=''):
    if path.startswith('api'): return abort(404)
    index_path = os.path.join(STATIC_FOLDER, 'index.html')
    if os.path.exists(index_path):
        return send_from_directory(STATIC_FOLDER, 'index.html')
    return "Configure static/index.html", 404

@app.route('/api/signal')
def api_signal():
    predictor.scrape_bc_game(predictor.current_table)
    return jsonify(predictor.predict_next())

@app.route('/api/history')
def api_history():
    history = []
    for r in predictor.history[-25:]:
        color = 'bg-red-500' if r==1 else 'bg-blue-500' if r==0 else 'bg-green-500'
        label = 'B' if r==1 else 'P' if r==0 else 'T'
        history.append({'result': label, 'color': color})
    return jsonify(history)

@app.route('/api/stats')
def api_stats():
    return jsonify(predictor.stats)

@app.route('/api/add_result', methods=['POST'])
def api_add():
    data = request.json or {}
    result = data.get('result', '').upper()
    if result in ['BANKER', 'PLAYER', 'TIE']:
        predictor.add_result(result)
        return jsonify({'success': True})
    return jsonify({'error': 'Invalid'}), 400

@app.route('/api/change_table', methods=['POST'])
def change_table():
    data = request.json or {}
    table = data.get('table', 'Baccarat 1')
    if table in BC_GAME_TABLES:
        predictor.current_table = table
        predictor.scrape_bc_game(table)
        return jsonify({'table': table, 'success': True})
    return jsonify({'error': 'Invalid table'}), 400

def auto_scrape():
    def run():
        predictor.scrape_bc_game(predictor.current_table)
        Timer(25.0, run).start()
    run()

if __name__ == '__main__':
    Thread(target=auto_scrape, daemon=True).start()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)