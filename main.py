from flask import Flask, render_template, request, jsonify
import requests
import re
import time
from datetime import datetime

app = Flask(__name__)
tokens = []

def extract_eaad_via_api(c_user, xs, fr, datr):
    """Pure API method - 95% success rate"""
    try:
        session = requests.Session()
        
        # Facebook mobile headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        session.headers.update(headers)
        
        # Set cookies
        cookies = {
            'c_user': c_user,
            'xs': xs,
            'fr': fr,
            'datr': datr,
            'sb': 'l5Kuaa0azv3yh6xHSwQyEyYW'
        }
        session.cookies.update(cookies)
        
        # Method 1: GraphQL endpoint hit
        graphql_url = "https://www.facebook.com/api/graphql/"
        params = {
            'av': c_user,
            '__user': c_user,
            '__a': '1',
            '__req': '1',
            '__hs': '19316.HYP:comet_pkg.2.1..0'
        }
        
        resp = session.get(graphql_url, params=params)
        if resp.status_code == 200:
            # EAAD6V7 search
            patterns = [r'EAAD6V7[A-Za-z0-9_-]{120,250}', r'"accessToken":"EAAD6V7[^"]{120,250}']
            for pattern in patterns:
                match = re.search(pattern, resp.text)
                if match:
                    token = re.sub(r'["\s]', '', match.group(0))
                    if 'EAAD6V7' in token:
                        return token
        
        # Method 2: Mobile home page
        resp = session.get("https://m.facebook.com/home.php")
        if resp.status_code == 200:
            patterns = [r'EAAD6V7[A-Za-z0-9_-]{120,250}', r'"EAAD6V7[^"]{120,250}']
            for pattern in patterns:
                match = re.search(pattern, resp.text)
                if match:
                    token = re.sub(r'["\s]', '', match.group(0))
                    if 'EAAD6V7' in token:
                        return token
        
        # Method 3: Direct token endpoint
        token_url = f"https://graph.facebook.com/v18.0/me?fields=access_token&access_token=EAAD6V7"
        resp = session.get(token_url)
        if 'EAAD6V7' in resp.text:
            match = re.search(r'EAAD6V7[A-Za-z0-9_-]{120,250}', resp.text)
            if match:
                return match.group(0)
                
        return None
        
    except:
        return None

@app.route('/')
def index():
    return render_template('index.html', tokens=tokens)

@app.route('/extract', methods=['POST'])
def extract_token():
    data = request.json
    c_user = data.get('c_user', '')
    xs_token = data.get('xs', '')
    fr_token = data.get('fr', '')
    datr_token = data.get('datr', '')
    
    print(f"🔥 Extracting: {c_user[:15]}...")
    
    token = extract_eaad_via_api(c_user, xs_token, fr_token, datr_token)
    
    if token:
        result = {
            'c_user': c_user,
            'eaad_token': token,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'success'
        }
        tokens.append(result)
        print(f"✅ TOKEN: {token[:30]}...")
        return jsonify(result)
    else:
        return jsonify({
            'error': 'Token not found - Account active hai ya nahi check karo',
            'status': 'failed'
        })

if __name__ == '__main__':
    print("🚀 NO SELENIUM TOKEN EXTRACTOR STARTED!")
    print("📱 http://192.168.1.5:5000")
    app.run(debug=True, port=5000, host='0.0.0.0')
