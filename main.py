from flask import Flask, render_template, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import time
import re
from datetime import datetime

app = Flask(__name__)
tokens = []

def setup_stealth_driver():
    chrome_options = Options()
    
    # Stealth options to avoid detection
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-plugins-discovery")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--allow-running-insecure-content")
    chrome_options.add_argument("--disable-features=VizDisplayCompositor")
    
    # User agent realistic banao
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # Headless mode OFF rakho pehle testing ke liye (comment kar sakte ho)
    # chrome_options.add_argument("--headless")
    
    # Experimental options
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # Auto ChromeDriver setup
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # Extra stealth script
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
    driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']})")
    
    return driver

def extract_eaad_token(driver, c_user):
    try:
        print("Starting extraction for C_user:", c_user[:20] + "...")
        
        # Facebook pe jaao
        driver.get("https://m.facebook.com/")
        time.sleep(4)
        
        # Cookie set karo
        driver.add_cookie({
            'name': 'c_user', 
            'value': c_user, 
            'domain': '.facebook.com',
            'path': '/',
            'secure': True
        })
        
        # Refresh karo cookie load hone ke liye
        driver.refresh()
        time.sleep(5)
        
        # Mobile Facebook pe token dhundho (better success rate)
        driver.get("https://m.facebook.com/")
        time.sleep(4)
        
        # Multiple extraction methods
        page_source = driver.page_source
        
        # Method 1: Direct EAAD6V7 search
        eaad_patterns = [
            r'"EAAD6V7[^"]*"',
            r'EAAD6V7[^",}]*',
            r'"accessToken":"EAAD6V[^"]*"',
            r'EAAD6V[^",}]*'
        ]
        
        for pattern in eaad_patterns:
            match = re.search(pattern, page_source, re.IGNORECASE)
            if match:
                token = match.group(0).strip('"')
                if len(token) > 50:  # Valid token length check
                    print("Token found via regex:", token[:30] + "...")
                    return token
        
        # Method 2: GraphQL requests check
        driver.get("https://m.facebook.com/home.php")
        time.sleep(3)
        
        page_source = driver.page_source
        for pattern in eaad_patterns:
            match = re.search(pattern, page_source, re.IGNORECASE)
            if match:
                token = match.group(0).strip('"')
                if len(token) > 50:
                    print("Token found via GraphQL:", token[:30] + "...")
                    return token
        
        print("No EAAD6V7 token found")
        return None
        
    except Exception as e:
        print(f"Extraction error: {e}")
        return None

@app.route('/')
def index():
    return render_template('index.html', tokens=tokens)

@app.route('/extract', methods=['POST'])
def extract_token():
    data = request.json
    c_user = data.get('c_user')
    
    if not c_user or len(c_user) < 10:
        return jsonify({'error': 'Valid C_user cookie required (min 10 chars)'}), 400
    
    try:
        print(f"New extraction request for C_user: {c_user[:20]}...")
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
            print("✅ Token extracted successfully!")
            return jsonify(token_data)
        else:
            return jsonify({
                'error': 'EAAD6V7 token not found. Try valid active C_user cookie.',
                'status': 'failed',
                'hint': 'Make sure C_user is from active logged-in session'
            })
            
    except Exception as e:
        print(f"❌ Critical error: {e}")
        return jsonify({'error': f'Extraction failed: {str(e)}', 'status': 'error'})

if __name__ == '__main__':
    print("🚀 Starting Facebook Token Extractor Panel...")
    print("📱 Visit: http://localhost:5000")
    app.run(debug=True, port=5000, host='0.0.0.0')
