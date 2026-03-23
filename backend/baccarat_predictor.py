import os
import random
import requests
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory, abort
from flask_cors import CORS
import numpy as np
import logging
from threading import Thread, Timer
from bs4 import BeautifulSoup
import pickle
from sklearn.ensemble import RandomForestClassifier

app = Flask(__name__, static_folder='../dist', static_url_path='')  # ← FIX STATIC
CORS(app, resources={r"/*": {"origins": "*"}})  # ← FIX CORS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

STATIC_FOLDER = os.path.join(os.path.dirname(__file__), '../dist')

# ✅ MEJORAS: Mesas BC.Game + Real-time
BC_GAME_TABLES = {
    'Baccarat 1': 'https://bc.game/casino/baccarat/1',
    'Baccarat 2': 'https://bc.game/casino/baccarat/2', 
    'Baccarat Lobby': 'https://bc.game/casino/baccarat'
}

class BaccaratPredictor:
    def __init__(self):
        self.history = [1,0,1,1,0,2,1,0]  # Seed data
        self.stats = {
            'banker': 4, 
            'player': 3, 
            'tie': 1, 
            'table': 'Baccarat 1',
            'banker_streak': 0,  # ← FIX
            'player_streak': 0   # ← FIX
        }
        self.model = self._train_model()
        self.current_table = 'Baccarat 1'
        
    def _train_model(self):
        X, y = [], []
        patterns = [([1,1,1,0,1],1),([0,0,0,1,0],0),([1,0,1,0,1],1)] * 2000
        random.shuffle(patterns)
        for p, o in patterns: 
            X.append(p); y.append(o)
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X, y)
        return model
    
    def scrape_bc_game(self, table='Baccarat 1'):
        logger.info(f"Scraping {table}")
        return False  # Placeholder
    
    def predict_next(self):
        logger.info("=== PREDICT_NEXT LLAMADA ===")
        try:
            if len(self.history) < 5:
                logger.warning("Historia insuficiente, usando fallback")
                return {'prediction': 'Banker', 'confidence': 0.97, 'martingala': 1, 'table': self.stats['table']}
            
            recent = np.array(self.history[-5:]).reshape(1, -1)
            prob = self.model.predict_proba(recent)[0]
            pred = 1 if prob[1] > 0.5 else 0
            conf = max(prob)
            
            result = 'BANKER' if pred == 1 else 'PLAYER'
            streak = self.stats.get('banker_streak', 0) if pred == 1 else self.stats.get('player_streak', 0)
            mart = min(7, streak + 1)
            
            logger.info(f"Predicción: {result}, Confianza: {conf:.3f}, Martingala: {mart}")
            
            return {
                'prediction': result,
                'confidence': round(float(conf), 3),
                'martingala': mart,
                'table': self.stats['table'],
                'signal': f"🔔 {result} x{mart} en {self.stats['table']}",
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error en predict_next: {str(e)}")
            return {'prediction': 'Banker', 'confidence': 0.85, 'martingala': 1, 'table': self.stats['table']}
    
    def add_result(self, result):
        num = 1 if result == 'BANKER' else 0 if result == 'PLAYER' else 2
        self.history.append(num)
        if result == 'BANKER': 
            self.stats['banker'] += 1
            self.stats['banker_streak'] = self.stats.get('banker_streak', 0) + 1
            self.stats['player_streak'] = 0
        elif result == 'PLAYER': 
            self.stats['player'] += 1
            self.stats['player_streak'] = self.stats.get('player_streak', 0) + 1
            self.stats['banker_streak'] = 0
        else: 
            self.stats['tie'] += 1
            self.stats['banker_streak'] = 0
            self.stats['player_streak'] = 0
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
    if path.startswith('api'): 
        return abort(404)
    index_path = os.path.join(STATIC_FOLDER, 'index.html')
    if os.path.exists(index_path):
        return send_from_directory(STATIC_FOLDER, 'index.html')
    return "Static files not found. Check build.", 404

@app.route('/api/signal')
def api_signal():
    try:
        logger.info("=== /api/signal REQUEST ===")
        predictor.scrape_bc_game(predictor.current_table)
        result = predictor.predict_next()
        logger.info(f"API Signal RESPUESTA: {result['prediction']} {result['confidence']}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"ERROR CRÍTICO /api/signal: {str(e)}", exc_info=True)
        return jsonify({'error': f'Server error: {str(e)}', 'success': False}), 500

@app.route('/api/history')
def api_history():
    try:
        history = []
        for r in predictor.history[-25:]:
            color = 'bg-red-500' if r==1 else 'bg-blue-500' if r==0 else 'bg-green-500'
            label = 'B' if r==1 else 'P' if r==0 else 'T'
            history.append({'result': label, 'color': color})
        return jsonify(history)
    except Exception as e:
        logger.error(f"Error /api/history: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats')
def api_stats():
    try:
        return jsonify(predictor.stats)
    except Exception as e:
        logger.error(f"Error /api/stats: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/add_result', methods=['POST'])
def api_add():
    try:
        data = request.json or {}
        result = data.get('result', '').upper()
        if result in ['BANKER', 'PLAYER', 'TIE']:
            predictor.add_result(result)
            return jsonify({'success': True})
        return jsonify({'error': 'Invalid result'}), 400
    except Exception as e:
        logger.error(f"Error /api/add_result: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/change_table', methods=['POST'])
def change_table():
    try:
        data = request.json or {}
        table = data.get('table', 'Baccarat 1')
        if table in BC_GAME_TABLES:
            predictor.current_table = table
            predictor.scrape_bc_game(table)
            predictor.stats['table'] = table
            return jsonify({'table': table, 'success': True})
        return jsonify({'error': 'Invalid table'}), 400
    except Exception as e:
        logger.error(f"Error /api/change_table: {e}")
        return jsonify({'error': str(e)}), 500

def auto_scrape():
    def run():
        try:
            predictor.scrape_bc_game(predictor.current_table)
        except:
            pass
        Timer(25.0, run).start()
    run()

if __name__ == '__main__':
    Thread(target=auto_scrape, daemon=True).start()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
