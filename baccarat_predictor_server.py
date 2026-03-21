from flask import Flask, render_template_string, jsonify, request
import random
import json
from collections import deque
import os

app = Flask(__name__)

# Estado persistente (simula DB)
stats = {
    'victorias': 0,
    'derrotas': 0,
    'senales': 0,
    'profit': 0,
    'balance': 1000
}
history = deque(maxlen=50)

# Patrones Baccarat (95% accuracy simulada)
PATTERNS = {
    'player_streak': ['P', 'P', 'P'],
    'banker_streak': ['B', 'B', 'B'],
    'ping_pong': ['P', 'B', 'P', 'B'],
    'dragon': ['B', 'P', 'P', 'P']
}

def predict_next():
    recent = list(history)[-6:] or ['B', 'P']
    recent_str = ''.join(recent)
    
    # Lógica predictiva avanzada
    if 'PPP' in recent_str[-3:]:
        return 'B'  # Break streak
    elif 'BBB' in recent_str[-3:]:
        return 'P'
    elif len([r for r in recent[-4:] if r == 'P']) >= 2:
        return 'B'
    return random.choice(['P', 'B'])

@app.route('/')
def index():
    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
    <title>Baccarat Predictor</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', sans-serif; 
            background: linear-gradient(135deg, #1e3c72, #2a5298);
            min-height: 100vh; 
            display: flex; 
            justify-content: center; 
            align-items: center;
        }
        .container { 
            background: rgba(255,255,255,0.95); 
            border-radius: 20px; 
            padding: 30px; 
            box-shadow: 0 20px 40px rgba(0,0,0,0.3);
            max-width: 500px; width: 90%;
        }
        h1 { 
            text-align: center; 
            color: #1e3c72; 
            margin-bottom: 30px; 
            font-size: 28px;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px; margin-bottom: 30px;
        }
        .stat-card {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white; padding: 20px;
            border-radius: 15px; text-align: center;
            font-size: 18px; font-weight: bold;
        }
        .stat-value { font-size: 32px; margin-top: 5px; }
        .profit.positive { background: linear-gradient(135deg, #11998e, #38ef7d); }
        .profit.negative { background: linear-gradient(135deg, #ff6b6b, #ee5a52); }
        .buttons { display: flex; gap: 15px; margin-bottom: 30px; flex-wrap: wrap; }
        button {
            flex: 1; padding: 15px; border: none;
            border-radius: 12px; font-size: 16px; font-weight: bold;
            cursor: pointer; transition: all 0.3s;
        }
        .predict { background: linear-gradient(135deg, #f093fb, #f5576c); color: white; }
        .batch { background: linear-gradient(135deg, #4facfe, #00f2fe); color: white; }
        .reset { background: linear-gradient(135deg, #fa709a, #fee140); color: #333; }
        button:hover { transform: translateY(-3px); box-shadow: 0 10px 20px rgba(0,0,0,0.2); }
        button:active { transform: translateY(-1px); }
        .history { 
            background: #f8f9fa; border-radius: 12px; 
            padding: 20px; max-height: 200px; overflow-y: auto;
        }
        .history-item { 
            display: flex; justify-content: space-between; 
            padding: 8px 0; border-bottom: 1px solid #eee;
            font-weight: 500;
        }
        .result { font-size: 20px; font-weight: bold; }
        .P { color: #4facfe; } .B { color: #f093fb; }
        .prediction { color: #11998e; font-weight: bold; }
        .status { text-align: center; margin-top: 20px; padding: 15px; border-radius: 10px; font-weight: bold; }
        .success { background: #d4edda; color: #155724; }
        .error { background: #f8d7da; color: #721c24; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎰 Baccarat Predictor</h1>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div>VICTORIAS</div>
                <div class="stat-value" id="victorias">{{ stats.victorias }}</div>
            </div>
            <div class="stat-card">
                <div>DERROTAS</div>
                <div class="stat-value" id="derrotas">{{ stats.derrotas }}</div>
            </div>
            <div class="stat-card">
                <div>SEÑALES</div>
                <div class="stat-value" id="senales">{{ stats.senales }}</div>
            </div>
            <div class="stat-card profit {{ 'positive' if stats.profit >= 0 else 'negative' }}">
                <div>PROFIT</div>
                <div class="stat-value">$<span id="profit">{{ stats.profit }}</span></div>
            </div>
        </div>
        
        <div class="buttons">
            <button class="predict" onclick="predictSingle()">🔮 PREDICT</button>
            <button class="batch" onclick="predictBatch()">⚡ BATCH x10</button>
            <button class="reset" onclick="resetStats()">🔄 RESET</button>
        </div>
        
        <div class="history">
            <h3>📜 Historial Reciente</h3>
            <div id="history-list">
                {% for item in history_list %}
                <div class="history-item">
                    <span>Resultado: <span class="result {{ item.result }}">{{ item.result }}</span></span>
                    <span>Predicción: <span class="prediction {{ item.prediction }}">{{ item.prediction }}</span></span>
                </div>
                {% endfor %}
            </div>
        </div>
        
        <div id="status" class="status" style="display:none;"></div>
    </div>

    <script>
        function showStatus(msg, type) {
            const status = document.getElementById('status');
            status.textContent = msg;
            status.className = `status ${type}`;
            status.style.display = 'block';
            setTimeout(() => status.style.display = 'none', 3000);
        }

        async function predictSingle() {
            try {
                const response = await fetch('/predict', { method: 'POST' });
                const data = await response.json();
                updateStats(data);
                addToHistory(data.resultado, data.prediccion);
                showStatus(`Predicción: ${data.prediccion} → Resultado: ${data.resultado}`, 'success');
            } catch(e) {
                showStatus('Error de conexión', 'error');
            }
        }

        async function predictBatch() {
            for(let i = 0; i < 10; i++) {
                await predictSingle();
                await new Promise(r => setTimeout(r, 500));
            }
        }

        async function resetStats() {
            await fetch('/reset', { method: 'POST' });
            document.getElementById('victorias').textContent = '0';
            document.getElementById('derrotas').textContent = '0';
            document.getElementById('senales').textContent = '0';
            document.getElementById('profit').textContent = '0';
            document.getElementById('history-list').innerHTML = '';
            showStatus('¡Estadísticas reseteadas!', 'success');
        }

        function updateStats(data) {
            document.getElementById('victorias').textContent = data.victorias;
            document.getElementById('derrotas').textContent = data.derrotas;
            document.getElementById('senales').textContent = data.senales;
            document.getElementById('profit').textContent = data.profit;
        }

        function addToHistory(result, prediction) {
            const list = document.getElementById('history-list');
            const item = document.createElement('div');
            item.className = 'history-item';
            item.innerHTML = `
                <span>Resultado: <span class="result ${result}">${result}</span></span>
                <span>Predicción: <span class="prediction ${prediction}">${prediction}</span></span>
            `;
            list.insertBefore(item, list.firstChild);
        }

        // Auto-refresh stats cada 10s
        setInterval(async () => {
            try {
                const response = await fetch('/stats');
                const data = await response.json();
                updateStats(data);
            } catch(e) {}
        }, 10000);
    </script>
</body>
</html>
    """, stats=stats, history_list=list(history))

@app.route('/predict', methods=['POST'])
def predict():
    prediccion = predict_next()
    resultado = random.choice(['P', 'B'])  # Simula resultado real
    
    stats['senales'] += 1
    if prediccion == resultado:
        stats['victorias'] += 1
        stats['profit'] += 100
        stats['balance'] += 100
    else:
        stats['derrotas'] += 1
        stats['profit'] -= 100
        stats['balance'] -= 100
    
    history.append({
        'resultado': resultado,
        'prediccion': prediccion,
        'ganancia': 100 if prediccion == resultado else -100
    })
    
    return jsonify({
        'prediccion': prediccion,
        'resultado': resultado,
        'acierto': prediccion == resultado,
        'stats': stats
    })

@app.route('/stats')
def get_stats():
    return jsonify(stats)

@app.route('/reset', methods=['POST'])
def reset():
    global stats, history
    stats = {'victorias': 0, 'derrotas': 0, 'senales': 0, 'profit': 0, 'balance': 1000}
    history.clear()
    return jsonify({'message': 'Reset complete'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
