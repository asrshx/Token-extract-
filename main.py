from flask import Flask, render_template, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
import time
import re
from datetime import datetime

app = Flask(__name__)
tokens = []

def setup_stealth_driver():
    chrome_options = Options()
    
    # Basic stealth
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # AUTO ChromeDriver fix - Latest stable version
    service = Service(ChromeDriverManager(chrome_type=ChromeType.GOOGLE).install())
    
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def extract_eaad_token(driver, c_user):
    try:
        print(f"🔍 Extracting for C_user: {c_user[:15]}...")
        
        # Direct Facebook mobile
        driver.get("https://m.facebook.com/")
        time.sleep(3)
        
        # Set multiple cookies for better success
        cookies = {
            'c_user': c_user,
            'datr': 'j5KuaThGz5SLh24wyTJKsdHk',
            'xs': '29%3AH0yv4meueN30jw%3A2%3A1773168528%3A-1%3A-1',
            'fr': '0je0muHPfIt1TR1ZE.AWd9K7Xxalu6Ok8qQBGcqz7aV1xVafYH-sJk1HJ21Zm2cPWQI2M.Bpq27i..AAA.0.0.BpsGeX.AWcdRlyIsCnhvTaZEI0_N66LmbA'
        }
        
        for name, value in cookies.items():
            driver.add_cookie({'name': name, 'value': value, 'domain': '.facebook.com'})
        
        driver.refresh()
        time.sleep(5)
        
        # Multiple pages check karo
        pages = [
            "https://m.facebook.com/home.php",
            "https://m.facebook.com/",
            "https://www.facebook.com/"
        ]
        
        all_source = ""
        for url in pages:
            driver.get(url)
            time.sleep(2)
            all_source += driver.page_source
        
        # Advanced EAAD6V7 regex
        patterns = [
            r'EAAD6V7[A-Za-z0-9_-]{100,250}',
            r'"EAAD6V7[^"]{100,250}"',
            r'EAAD6V7[^",}]{100,250}',
            r'accessToken["\s:]*"EAAD6V7[^"]*"'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, all_source, re.IGNORECASE)
            for match in matches:
                token = re.sub(r'["\s]', '', match)
                if len(token) > 150 and 'EAAD6V7' in token:
                    print(f"✅ TOKEN FOUND: {token[:30]}...")
                    return token
        
        print("❌ No token found")
        return None
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

@app.route('/')
def index():
    return render_template('index.html', tokens=tokens)

@app.route('/extract', methods=['POST'])
def extract_token():
    data = request.json
    c_user = data.get('c_user')
    
    if not c_user:
        return jsonify({'error': 'C_user required'}), 400
    
    try:
        driver = setup_stealth_driver()
        token = extract_eaad_token(driver, c_user)
        driver.quit()
        
        if token:
            result = {
                'c_user': c_user,
                'eaad_token': token,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'status': 'success'
            }
            tokens.append(result)
            return jsonify(result)
        else:
            return jsonify({
                'error': 'EAAD6V7 not found. Try another fresh C_user',
                'status': 'failed'
            })
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'})

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
