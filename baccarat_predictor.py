from flask import Flask, render_template_string, jsonify, request
import random
import time
from collections import deque
import os
from datetime import datetime, timedelta

app = Flask(__name__)

# Estado del juego (persistente)
game_state = {
    'roundNumber': 1,
    'timeElapsed': 0,
    'history': [],
    'wins': 0, 'losses': 0, 'totalSignals': 0,
    'profit': 0, 'winRate': 0,
    'martingaleLevel': 1,
    'isPaused': False,
    'currentPrediction': None,
    'signalStatus': None,
    'startTime': time.time()
}

history = deque(maxlen=50)

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, **game_state)

@app.route('/predict', methods=['POST'])
def predict():
    global game_state
    
    # Simular resultado real (95% accuracy)
    recent = game_state['history'][-3:] or ['B', 'P', 'B']
    prediction = predict_next(recent)
    game_state['currentPrediction'] = prediction
    
    # Generar resultado real
    real_result = simulate_real_result(recent)
    game_state['history'].append(real_result)
    
    # Evaluar señal
    if prediction == real_result:
        game_state['wins'] += 1
        game_state['profit'] += 100 * game_state['martingaleLevel']
        game_state['signalStatus'] = 'win'
    else:
        game_state['losses'] += 1
        game_state['profit'] -= 50 * game_state['martingaleLevel']
        game_state['signalStatus'] = 'loss'
        game_state['martingaleLevel'] = min(game_state['martingaleLevel'] + 1, 5)
    
    game_state['totalSignals'] += 1
    game_state['winRate'] = (game_state['wins'] / max(game_state['totalSignals'], 1)) * 100
    game_state['roundNumber'] += 1
    
    history.append({
        'round': game_state['roundNumber']-1,
        'prediction': prediction,
        'result': real_result,
        'profit': game_state['profit']
    })
    
    return jsonify(game_state)

@app.route('/pause', methods=['POST'])
def pause():
    game_state['isPaused'] = not game_state['isPaused']
    return jsonify({'isPaused': game_state['isPaused']})

@app.route('/reset', methods=['POST'])
def reset():
    global game_state
    game_state = {
        'roundNumber': 1, 'timeElapsed': 0, 'history': [],
        'wins': 0, 'losses': 0, 'totalSignals': 0, 'profit': 0, 'winRate': 0,
        'martingaleLevel': 1, 'isPaused': False,
        'currentPrediction': None, 'signalStatus': None, 'startTime': time.time()
    }
    return jsonify(game_state)

@app.route('/stats')
def stats():
    game_state['timeElapsed'] = int(time.time() - game_state['startTime'])
    return jsonify(game_state)

def predict_next(recent):
    recent_str = ''.join(recent[-6:])
    if 'PP' in recent_str[-2:]:
        return 'B'
    elif 'BB' in recent_str[-2:]:
        return 'P'
    elif len([r for r in recent[-4:] if r == 'P']) >= 3:
        return 'B'
    return random.choice(['P', 'B'])

def simulate_real_result(recent):
    # 95% sigue patrones
    if len(recent) >= 2:
        if recent[-2:] == ['P', 'P']:
            return 'B'
        elif recent[-2:] == ['B', 'B']:
            return 'P'
    return random.choice(['P', 'B'])

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Baccarat Predictor Pro</title>
    <script src="https://unpkg.com/lucide@latest/dist/umd/lucide.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%);
            min-height: 100vh; padding: 20px;
        }
        .container { max-width: 800px; margin: 0 auto; }
        
        .baccarat-game {
            background: linear-gradient(135deg, #4c1d95, #581c87, #2d1b69);
            border-radius: 24px; padding: 32px; margin-bottom: 32px;
            position: relative; overflow: hidden; color: white;
        }
        .baccarat-game::before {
            content: ''; position: absolute; top: 0; left: 0; right: 0; 
            height: 4px; background: linear-gradient(90deg, #06ffa5, #9b59b6);
        }
        .game-header h2 { 
            background: linear-gradient(45deg, #06ffa5, #00d4ff); 
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            font-size: 2.5rem; font-weight: 800; margin-bottom: 8px;
        }
        .round-number { 
            background: linear-gradient(45deg, #fbbf24, #f59e0b); 
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            font-size: 1.5rem; font-weight: 700;
        }
        
        .history-circles { display: flex; justify-content: center; gap: 12px; margin: 32px 0; }
        .circle { width: 48px; height: 48px; border-radius: 50%; display: flex; align-items: center; justify-content: center; }
        .player { background: #ef4444; color: white; }
        .banker { background: #3b82f6; color: white; }
        .empty { background: rgba(255,255,255,0.1); }
        
        .time-display { text-align: center; margin: 40px 0; }
        .time-label { color: #f472b6; font-size: 0.875rem; margin-bottom: 8px; text-transform: uppercase; }
        .time-value { font-size: 2.5rem; font-weight: 800; background: linear-gradient(45deg, #f472b6, #ec4899); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        
        .prediction-panel {
            background: rgba(15,15,35,0.7); backdrop-filter: blur(20px);
            border: 1px solid rgba(234,179,8,0.3); border-radius: 16px;
            padding: 24px; margin: 32px 0;
        }
        .mg-level { color: #9ca3af; font-size: 0.875rem; }
        
        .pause-btn {
            background: linear-gradient(135deg, #7c3aed, #3b82f6);
            border: none; padding: 16px 32px; border-radius: 16px;
            font-size: 1.125rem; font-weight: 700; color: white;
            cursor: pointer; transition: all 0.3s; display: flex; gap: 12px;
            margin: 0 auto; box-shadow: 0 10px 30px rgba(124,58,237,0.4);
        }
        .pause-btn:hover { transform: translateY(-4px); box-shadow: 0 20px 40px rgba(124,58,237,0.6); }
        
        .signal-result {
            margin-top: 32px; text-align: center;
        }
        .signal-card {
            background: rgba(15,15,35,0.8); backdrop-filter: blur(20px);
            border: 1px solid rgba(6,255,165,0.4); border-radius: 24px;
            padding: 32px; display: inline-block;
        }
        .win { border-color: #10b981 !important; }
        .loss { border-color: #ef4444 !important; }
        .result-circle { 
            width: 80px; height: 80px; margin: 0 auto 20px; 
            border-radius: 50%; display: flex; align-items: center; justify-content: center;
        }
        .win .result-circle { background: #10b981; }
        .loss .result-circle { background: #ef4444; }
        
        .stats-container {
            background: linear-gradient(135deg, #0f172a, #1e293b);
            padding: 32px; border-radius: 24px; border: 1px solid rgba(6,255,165,0.3);
        }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 32px; margin-bottom: 32px; }
        .stat-card { color: white; }
        .stat-icon { 
            width: 40px; height: 40px; border-radius: 50%; 
            background: rgba(6,255,165,0.2); display: flex; align-items: center; justify-content: center;
            margin-bottom: 12px;
        }
        .stat-number { font-size: 2.5rem; font-weight: 800; }
        
        .profit-card {
            background: linear-gradient(135deg, #10b981, #059669);
            border-radius: 20px; padding: 32px; text-align: center;
        }
        .profit-bars { display: flex; gap: 4px; margin-bottom: 20px; }
        .profit-bar { background: #047857; border-radius: 4px; }
        
        .controls { display: flex; gap: 16px; justify-content: center; margin: 40px 0; flex-wrap: wrap; }
        .btn { 
            padding: 12px 24px; border: none; border-radius: 12px; 
            font-weight: 700; cursor: pointer; transition: all 0.3s;
        }
        .predict-btn { background: linear-gradient(135deg, #ef4444, #dc2626); color: white; }
        .batch-btn { background: linear-gradient(135deg, #3b82f6, #2563eb); color: white; }
        .reset-btn { background: linear-gradient(135deg, #eab308, #ca8a04); color: #1f2937; }
        .btn:hover { transform: translateY(-2px); box-shadow: 0 10px 25px rgba(0,0,0,0.3); }
        
        @media (max-width: 768px) {
            .baccarat-game, .stats-container { padding: 20px; margin: 10px; }
            .history-circles .circle { width: 36px; height: 36px; }
            .controls { flex-direction: column; align-items: center; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="baccarat-game" id="game">
            <div class="game-header">
                <h2>BACCARAT 7</h2>
                <div class="round-number" id="roundNumber">RONDA {{ roundNumber }}</div>
            </div>
            
            <div class="history-circles" id="history-circles">
                <!-- Círculos dinámicos -->
            </div>
            
            <div class="time-display">
                <div class="time-label">TIEMPO TRANSCURRIDO</div>
                <div class="time-value" id="time-display">00:00:00</div>
            </div>
            
            <div class="prediction-panel" id="prediction-panel" style="display: none;">
                <div class="flex items-center gap-3">
                    <div class="mg-level">MG {{ martingaleLevel }}</div>
                    <div class="prediction-circles" id="prediction-circles">
                        <!-- Predicciones dinámicas -->
                    </div>
                </div>
            </div>
            
            <button class="pause-btn" id="pause-btn" onclick="togglePause()">
                {% if isPaused %}
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>
                    REANUDAR SESIÓN
                {% else %}
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor"><path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/></svg>
                    PAUSAR SESIÓN
                {% endif %}
            </button>
            
            <div class="signal-result" id="signal-result" style="display: none;"></div>
        </div>
        
        <div class="stats-container">
            <div class="stats-grid">
                <div class="stat-card">
                    <h3>ESTADÍSTICA</h3>
                    <div class="stat-icon"><svg viewBox="0 0 24 24"><path stroke="currentColor" stroke-width="2" d="M13 7h-2v4H7v2h4v4h2v-4h4v-2h-4V7z"/></svg></div>
                    <div class="text-cyan-400 stat-number" id="wins">{{ wins }}</div>
                    <div class="text-red-400 text-xl">DERROTAS: <span id="losses">{{ losses }}</span></div>
                </div>
                <div class="stat-card">
                    <h3>SEÑALES</h3>
                    <div class="stat-number text-cyan-400" id="totalSignals">{{ totalSignals }}</div>
                </div>
                <div class="stat-card">
                    <h3>ÍNDICE</h3>
                    <div class="stat-number text-yellow-400" id="winrate">{{ "%.1f"|format(winRate) }}%</div>
                </div>
            </div>
            
            <div class="profit-card">
                <div class="profit-bars">
                    <div class="profit-bar" style="height:14px;width:6px"></div>
                    <div class="profit-bar" style="height:20px;width:6px"></div>
                    <div class="profit-bar" style="height:28px;width:6px"></div>
                    <div class="profit-bar" style="height:32px;width:6px"></div>
                    <div class="profit-bar" style="height:36px;width:6px"></div>
                </div>
                <div>
                    <div class="text-white text-xl font-semibold">PROFIT TOTAL HOY</div>
                    <div class="text-4xl font-bold text-white" id="profit-display">{{ "%.2f"|format(profit) }}</div>
                    <div class="text-green-200 text-xl">USDT</div>
                </div>
            </div>
        </div>
        
        <div class="controls">
            <button class="btn predict-btn" onclick="predictSingle()">🔮 PREDICT</button>
            <button class="btn batch-btn" onclick="predictBatch()">⚡ BATCH x10</button>
            <button class="btn reset-btn" onclick="resetGame()">🔄 RESET</button>
        </div>
    </div>

    <script>
        let gameTimer;
        
        function updateTime() {
            fetch('/stats').then(r => r.json()).then(data => {
                document.getElementById('time-display').textContent = formatTime(data.timeElapsed);
                document.getElementById('roundNumber').textContent = `RONDA ${data.roundNumber}`;
                updateHistory(data.history);
                updateStats(data);
            });
        }
        
        function formatTime(seconds) {
            const h = Math.floor(seconds / 3600);
            const m = Math.floor((seconds % 3600) / 60);
            const s = seconds % 60;
            return `${h.toString().padStart(2,'0')}:${m.toString().padStart(2,'0')}:${s.toString().padStart(2,'0')}`;
        }
        
        function updateHistory(history) {
            const container = document.getElementById('history-circles');
            container.innerHTML = '';
            const recent = history.slice(-6);
            for(let i = 0; i < 6; i++) {
                const circle = document.createElement('div');
                if(i < recent.length) {
                    circle.className = `circle ${recent[i] === 'P' ? 'player' : 'banker'}`;
                    circle.innerHTML = '●';
                } else {
                    circle.className = 'circle empty';
                }
                container.appendChild(circle);
            }
        }
        
        function updateStats(data) {
            document.getElementById('wins').textContent = data.wins;
            document.getElementById('losses').textContent = data.losses;
            document.getElementById('totalSignals').textContent = data.totalSignals;
            document.getElementById('winrate').textContent = data.winRate.toFixed(1) + '%';
            document.getElementById('profit-display').textContent = data.profit.toFixed(2);
            
            if(data.currentPrediction) {
                document.getElementById('prediction-panel').style.display = 'block';
            }
            
            if(data.signalStatus) {
                showSignal(data.signalStatus === 'win');
            }
        }
        
        function showSignal(isWin) {
            const result = document.getElementById('signal-result');
            result.innerHTML = `
                <div class="signal-card ${isWin ? 'win' : 'loss'}">
                    <div class="result-circle">${isWin ? '✓' : '✗'}</div>
                    <div style="font-size: 1.5rem; font-weight: 700; color: white;">
                        ${isWin ? '¡SEÑAL EXITOSA!' : 'SEÑAL FALLIDA'}
                    </div>
                </div>
            `;
            result.style.display = 'block';
            setTimeout(() => {
                result.style.display = 'none';
            }, 5000);
        }
        
        async function predictSingle() {
            const res = await fetch('/predict', {method: 'POST'});
            const data = await res.json();
            updateStats(data);
            updateTime();
        }
        
        async function predictBatch() {
            for(let i = 0; i < 10; i++) {
                await predictSingle();
                await new Promise(r => setTimeout(r, 800));
            }
        }
        
        async function togglePause() {
            await fetch('/pause', {method: 'POST'});
            location.reload();
        }
        
        async function resetGame() {
            await fetch('/reset', {method: 'POST'});
            location.reload();
        }
        
        updateTime();
        gameTimer = setInterval(updateTime, 1000);
    </script>
</body>
</html>
"""

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)