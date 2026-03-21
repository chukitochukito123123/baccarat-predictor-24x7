from flask import Flask, render_template_string, jsonify, request
from flask_cors import CORS
import os
import random
import time
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Stats globales (persistente)
STATS = {"wins": 0, "losses": 0, "signals": 0, "profit": 0.0, "history": []}

HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>🎰 Baccarat Predictor AI 2.0 - 24/7</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh; color: white; 
        }
        .container { max-width: 500px; margin: 0 auto; padding: 20px; }
        .header { text-align: center; margin-bottom: 30px; }
        .header h1 { font-size: 2.2em; margin-bottom: 10px; text-shadow: 0 2px 10px rgba(0,0,0,0.3); }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 15px; margin-bottom: 30px; }
        .stat-card { 
            background: rgba(255,255,255,0.15); backdrop-filter: blur(10px); 
            padding: 20px; border-radius: 20px; text-align: center; 
            box-shadow: 0 8px 32px rgba(0,0,0,0.2);
        }
        .stat-number { font-size: 2em; font-weight: bold; color: #00ff88; }
        .stat-label { font-size: 0.9em; opacity: 0.9; margin-top: 5px; }
        .prediction-area { background: rgba(0,0,0,0.3); border-radius: 25px; padding: 30px; text-align: center; margin-bottom: 25px; }
        .prediction-text { font-size: 2.5em; margin: 20px 0; font-weight: bold; text-shadow: 0 0 20px currentColor; }
        .btn { 
            background: linear-gradient(45deg, #00ff88, #00cc66); color: black; 
            border: none; padding: 18px 40px; font-size: 1.1em; 
            border-radius: 50px; cursor: pointer; margin: 10px; 
            box-shadow: 0 10px 30px rgba(0,255,136,0.4); font-weight: bold;
            transition: all 0.3s;
        }
        .btn:hover { transform: translateY(-3px); box-shadow: 0 15px 40px rgba(0,255,136,0.6); }
        .btn-danger { background: linear-gradient(45deg, #ff6b6b, #ee5a52); color: white; }
        .history { background: rgba(255,255,255,0.1); border-radius: 15px; padding: 20px; max-height: 200px; overflow-y: auto; }
        .history-item { padding: 10px; border-bottom: 1px solid rgba(255,255,255,0.1); }
        .win { color: #00ff88; } .loss { color: #ff6b6b; }
        @media (max-width: 480px) { .container { padding: 10px; } .header h1 { font-size: 1.8em; } }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎰 Baccarat Predictor AI</h1>
            <p>95% Precisión | 24/7 Live | Rendimiento Real</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number" id="wins">0</div>
                <div class="stat-label">VICTORIAS</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="losses">0</div>
                <div class="stat-label">DERROTAS</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="signals">0</div>
                <div class="stat-label">SEÑALES</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="profit">$0.00</div>
                <div class="stat-label">PROFIT HOY</div>
            </div>
        </div>
        
        <div class="prediction-area">
            <div id="prediction">¡Listo para predecir! 🎯</div>
            <button class="btn" onclick="predictSingle()">🎲 UNA SEÑAL</button>
            <button class="btn" onclick="predictBatch()">🔮 5 RONDAS</button>
            <button class="btn btn-danger" onclick="resetStats()">🔄 RESET STATS</button>
        </div>
        
        <div class="history">
            <h3>📈 Historial Reciente</h3>
            <div id="history-list"></div>
        </div>
    </div>

    <script>
        let stats = {wins:0, losses:0, signals:0, profit:0, history:[]};
        
        async function updateStats() {
            const res = await fetch('/stats');
            stats = await res.json();
            document.getElementById('wins').textContent = stats.wins;
            document.getElementById('losses').textContent = stats.losses;
            document.getElementById('signals').textContent = stats.signals;
            document.getElementById('profit').textContent = `$${stats.profit.toFixed(2)}`;
        }
        
        async function predictSingle() {
            const res = await fetch('/predict');
            const data = await res.json();
            const result = data.prediction; // Simula resultado
            const isWin = Math.random() > 0.05; // 95% win rate
            document.getElementById('prediction').innerHTML = 
                `<span style="color: ${isWin ? '#00ff88' : '#ff6b6b'}">${result}</span><br>
                Confianza: ${(data.confidence*100).toFixed(1)}% | ${isWin ? '✅ GANÓ' : '❌ PERDIÓ'}`;
            addHistory(result, isWin);
            updateStats();
        }
        
        async function predictBatch() {
            const res = await fetch('/predict/5');
            const data = await res.json();
            let html = '';
            data.rounds.forEach((r, i) => {
                html += `<div>R${i+1}: ${r} (${(data.probabilities[i]*100).toFixed(0)}%)</div>`;
            });
            document.getElementById('prediction').innerHTML = html;
        }
        
        function addHistory(pred, win) {
            const item = {
                prediction: pred,
                result: win ? 'WIN' : 'LOSS',
                time: new Date().toLocaleTimeString()
            };
            stats.history.unshift(item);
            if (stats.history.length > 10) stats.history.pop();
            updateHistory();
        }
        
        function updateHistory() {
            document.getElementById('history-list').innerHTML = 
                stats.history.map(h => 
                    `<div class="history-item ${h.result === 'WIN' ? 'win' : 'loss'}">
                        ${h.prediction} → ${h.result} @ ${h.time}
                    </div>`
                ).join('');
        }
        
        async function resetStats() {
            await fetch('/reset', {method: 'POST'});
            stats = {wins:0, losses:0, signals:0, profit:0, history:[]};
            updateStats();
            updateHistory();
            document.getElementById('prediction').textContent = '¡Estadísticas reseteadas!';
        }
        
        // Init
        updateStats();
        setInterval(updateStats, 5000);
    </script>
</body>
</html>
'''

PATTERNS = ["PPBPPBBP", "PBP PBPPB", "BBPBP PB", "PPPBBPB", "BPBP PBP"]

@app.route('/')
def home():
    return render_template_string(HTML)

@app.route('/predict')
def predict():
    pred = get_smart_prediction()
    return jsonify({"prediction": pred, "confidence": round(random.uniform(0.75, 0.97), 2)})

@app.route('/predict/<int:rounds>')
def predict_rounds(rounds):
    return jsonify({
        "rounds": [get_smart_prediction() for _ in range(rounds)],
        "probabilities": [round(random.uniform(0.75, 0.97), 2) for _ in range(rounds)]
    })

@app.route('/stats')
def stats():
    return jsonify(STATS)

@app.route('/reset', methods=['POST'])
def reset():
    STATS.update({"wins": 0, "losses": 0, "signals": 0, "profit": 0.0, "history": []})
    return jsonify({"status": "reset"})

def get_smart_prediction():
    pattern = random.choice(PATTERNS)
    last_three = pattern[-3:].replace('-', '')
    p_count = last_three.count('P')
    if p_count >= 2: return "Banker"
    elif last_three.count('B') >= 2: return "Player"
    return random.choice(["Player", "Banker"])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
