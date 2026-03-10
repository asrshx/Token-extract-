from flask import Flask, render_template, request, jsonify
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import threading
import json
import re
from datetime import datetime

app = Flask(__name__)

# Global storage for tokens
tokens = []

def setup_stealth_driver():
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--disable-features=VizDisplayCompositor")
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def extract_eaad_token(driver, c_user):
    try:
        # Facebook login page pe jaao
        driver.get("https://www.facebook.com/")
        time.sleep(3)
        
        # C_user cookie set karo
        driver.add_cookie({'name': 'c_user', 'value': c_user, 'domain': '.facebook.com'})
        driver.refresh()
        time.sleep(5)
        
        # Facebook pe navigate karo aur token dhundho
        driver.get("https://www.facebook.com/")
        time.sleep(3)
        
        # Page source se EAAD6V7 token extract karo
        page_source = driver.page_source
        eaad_match = re.search(r'"EAAD6V7[^"]+"', page_source)
        
        if eaad_match:
            eaad_token = eaad_match.group(0).strip('"')
            return eaad_token
        else:
            # Alternative method - network requests check karo
            for request in driver.requests:
                if 'EAAD6V7' in request.response.body:
                    token_match = re.search(r'EAAD6V7[^",}]*(?=["}]|$)', request.response.body)
                    if token_match:
                        return token_match.group(0)
        
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

@app.route('/')
def index():
    return render_template('index.html', tokens=tokens)

@app.route('/extract', methods=['POST'])
def extract_token():
    data = request.json
    c_user = data.get('c_user')
    
    if not c_user:
        return jsonify({'error': 'C_user cookie required'}), 400
    
    try:
        driver = setup_stealth_driver()
        token = extract_eaad_token(driver, c_user)
        driver.quit()
        
        if token:
            token_data = {
                'c_user': c_user,
                'eaad_token': token,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'status': 'success'
            }
            tokens.append(token_data)
            return jsonify(token_data)
        else:
            return jsonify({'error': 'EAAD6V7 token not found', 'status': 'failed'})
            
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
