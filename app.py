import time
import hashlib
import requests
import json
import urllib.parse
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Thông tin API lấy từ ảnh image_7bc9fc.png của bạn
APP_ID = "17336120000" 
APP_SECRET = "J4FFDFKVLDORHOXUE4UY3XMQRE6OMDWE"

def get_original_url(url):
    try:
        if "s.shopee.vn" in url or "shope.ee" in url:
            response = requests.head(url, allow_redirects=True, timeout=5)
            return response.url
        return url
    except:
        return url

def generate_shopee_link(origin_url):
    try:
        timestamp = int(time.time())
        # 1. ĐỔI ENDPOINT THEO ẢNH image_7a781c.png
        endpoint = "https://open-api.affiliate.shopee.vn/graphql"
        
        real_url = get_original_url(origin_url)
        
        # 2. SỬA QUERY THEO ĐÚNG MẪU (originUrl có chữ U hoa)
        query = """
        mutation($url: String!) {
            generateShortLink(input: {originUrl: $url}) {
                shortLink
            }
        }
        """
        variables = {"url": real_url}
        body = json.dumps({'query': query, 'variables': variables})
        
        # 3. TẠO CHỮ KÝ
        base_str = APP_ID + str(timestamp) + body + APP_SECRET
        signature = hashlib.sha256(base_str.encode('utf-8')).hexdigest()

        # 4. SỬA ĐỊNH DẠNG AUTHORIZATION (Có Credential và Signature)
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"SHA256 Credential={APP_ID}, Signature={signature}, Timestamp={timestamp}"
        }

        response = requests.post(endpoint, headers=headers, data=body, timeout=10)
        res_data = response.json()
        
        print("--- Phản hồi từ Shopee ---")
        print(json.dumps(res_data, indent=2))
        
        if 'data' in res_data and res_data['data'].get('generateShortLink'):
            return res_data['data']['generateShortLink']['shortLink']
        return None
    except Exception as e:
        print(f"Lỗi: {e}")
        return None

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/convert')
def convert():
    raw_url = request.args.get('url')
    if not raw_url:
        return jsonify({"error": "Vui lòng dán link!"})
    
    final_link = generate_shopee_link(raw_url)
    if final_link:
        return jsonify({"short_link": final_link})
    else:
        return jsonify({"error": "Link chưa được duyệt hoặc API bận. Thử lại sau nhé!"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)