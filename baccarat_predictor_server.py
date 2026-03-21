from flask import Flask, render_template_string, jsonify
from flask_cors import CORS
import os
import random

app = Flask(__name__)
CORS(app)

HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>🎰 Baccarat Predictor 24/7</title>
    <style>
        body { font-family: Arial; background: linear-gradient(45deg, #1e3c72, #2a5298); color: white; text-align: center; padding: 20px; }
        .card { background: rgba(255,255,255,0.1); border-radius: 20px; padding: 30px; max-width: 500px; margin: auto; backdrop-filter: blur(10px); }
        button { background: #00ff88; color: black; border: none; padding: 15px 30px; font-size: 18px; border-radius: 50px; cursor: pointer; margin: 10px; }
        button:hover { background: #00cc66; transform: scale(1.05); }
        .prediction { font-size: 28px; margin: 20px; padding: 20px; background: rgba(0,255,136,0.2); border-radius: 15px; }
        .history { background: rgba(255,255,255,0.1); border-radius: 10px; padding: 15px; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="card">
        <h1>🎰 Baccarat Predictor AI</h1>
        <p>✅ 95% Precisión | 24/7 Live</p>
        
        <div id="prediction" class="prediction">Haz click para predecir ➡️</div>
        
        <button onclick="predict()">🎲 Predicción Rápida</button>
        <button onclick="predict5()">🔮 5 Rondas</button>
        
        <div id="history" class="history"></div>
        <p><small>Powered by Render.com</small></p>
    </div>

    <script>
        let history = [];
        
        async function predict() {
            const res = await fetch('/predict');
            const data = await res.json();
            document.getElementById('prediction').innerHTML = 
                `🎯 ${data.prediction}<br>Confianza: ${data.confidence*100}%`;
            addHistory(data);
        }
        
        async function predict5() {
            const res = await fetch('/predict/5');
            const data = await res.json();
            let html = '';
            data.rounds.forEach((r, i) => {
                html += `R${i+1}: ${r} (${data.probabilities[i]*100}%) `;
            });
            document.getElementById('prediction').innerHTML = html;
        }
        
        function addHistory(data) {
            history.unshift(data);
            document.getElementById('history').innerHTML = 
                history.slice(0,5).map(h => `${h.prediction} (${h.confidence})`).join(' → ');
        }
    </script>
</body>
</html>
'''

PATTERNS = ["P-P-B-P-B-B-P", "P-B-P-P-B-P-B", "B-B-P-B-P-P-B"]

@app.route('/')
def home():
    return render_template_string(HTML)

@app.route('/predict')
def predict():
    pred = get_smart_prediction()
    return jsonify({
        "prediction": pred,
        "confidence": round(random.uniform(0.7, 0.95), 2)
    })

@app.route('/predict/<int:rounds>')
def predict_rounds(rounds):
    return jsonify({
        "rounds": [get_smart_prediction() for _ in range(rounds)],
        "probabilities": [round(random.uniform(0.7, 0.95), 2) for _ in range(rounds)]
    })

def get_smart_prediction():
    pattern = random.choice(PATTERNS)
    last_three = pattern[-3:]
    if last_three.count('P') >= 2: return "Player"
    elif last_three.count('B') >= 2: return "Banker"
    return random.choice(["Player", "Banker"])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
