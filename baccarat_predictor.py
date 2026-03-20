import os
import time
import json
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import threading

app = Flask(__name__)
CORS(app, origins=["*"])  # Permitir todas las conexiones para pruebas

# Variables globales
driver = None
is_scraping = False
current_stats = {
    "total_games": 0,
    "player_wins": 0,
    "banker_wins": 0,
    "tie": 0,
    "prediction": "Esperando...",
    "confidence": 0
}

def init_driver():
    """Inicializa Chrome completamente invisible y anti-detección"""
    global driver
    chrome_options = Options()
    
    # Headless 100% invisible (Chrome 109+)
    chrome_options.add_argument("--headless=new")
    
    # Anti-detección avanzada
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # User-Agent realista
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # Rendimiento y estabilidad
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-extensions")
    
    # Evitar detección WebGL/SwiftShader
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--disable-features=VizDisplayCompositor")
    
    driver = webdriver.Chrome(service=webdriver.chrome.service.Service(ChromeDriverManager().install()), options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    print("✅ Chrome Driver inicializado (100% invisible)")

def scrape_baccarat(url):
    """Scraping principal con anti-detección"""
    global current_stats, is_scraping
    
    try:
        print(f"🌐 Accediendo a: {url}")
        driver.get(url)
        
        # Esperar página cargada (anti-detección: tiempo realista)
        time.sleep(3 + (hash(url) % 2))  # Delay variable
        
        # Buscar resultados de Baccarat (ajusta selectores según bc.game)
        wait = WebDriverWait(driver, 10)
        
        # Ejemplo de selectores (AJUSTA según inspección real de bc.game)
        results = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".game-history li, .result-item, [data-result]")))
        
        player_wins = 0
        banker_wins = 0
        ties = 0
        
        for result in results[-20:]:  # Últimos 20 juegos
            result_text = result.text.lower()
            if "player" in result_text or "p" in result_text:
                player_wins += 1
            elif "banker" in result_text or "b" in result_text:
                banker_wins += 1
            elif "tie" in result_text or "empate" in result_text:
                ties += 1
        
        total = player_wins + banker_wins + ties
        current_stats = {
            "total_games": total,
            "player_wins": player_wins,
            "banker_wins": banker_wins,
            "tie": ties,
            "prediction": "Banker" if banker_wins > player_wins else "Player",
            "confidence": round(abs(banker_wins - player_wins) / total * 100, 1)
        }
        
        print(f"📊 Stats: {current_stats}")
        return True
        
    except Exception as e:
        print(f"❌ Error scraping: {str(e)}")
        current_stats["prediction"] = "Error"
        return False

@app.route('/')
def home():
    return jsonify({"status": "API Baccarat Predictor 24/7", "ready": driver is not None})

@app.route('/stats', methods=['GET'])
def get_stats():
    return jsonify(current_stats)

@app.route('/start_scraping', methods=['POST'])
def start_scraping():
    global is_scraping
    
    if is_scraping:
        return jsonify({"error": "Ya está scrapeando"}), 400
    
    data = request.json
    url = data.get('url', '')
    
    if not url:
        return jsonify({"error": "URL requerida"}), 400
    
    is_scraping = True
    
    def scraping_thread():
        global is_scraping
        success = scrape_baccarat(url)
        is_scraping = False
        if success:
            return jsonify(current_stats)
        else:
            return jsonify({"error": "Error en scraping"}), 500
    
    # Ejecutar en thread para no bloquear Flask
    thread = threading.Thread(target=lambda: scraping_thread())
    thread.start()
    
    return jsonify({"status": "Iniciando scraping...", "url": url})

@app.route('/stop_scraping', methods=['POST'])
def stop_scraping():
    global is_scraping
    is_scraping = False
    return jsonify({"status": "Scraping detenido"})

if __name__ == '__main__':
    try:
        init_driver()
        # Puerto configurable para Render (por defecto 8080)
        port = int(os.environ.get('PORT', 8080))
        app.run(host='0.0.0.0', port=port, debug=False)
    except KeyboardInterrupt:
        print("🛑 Cerrando...")
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass