import time
import hashlib
import requests
import json
import os
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Thông tin API Shopee
APP_ID = "17336120000" 
APP_SECRET = "J4FFDFKVLDORHOXUE4UY3XMQRE6OMDWE"

def get_original_url(url):
    try:
        if "s.shopee.vn" in url or "shope.ee" in url or "shopee.vn" in url:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.head(url, allow_redirects=True, timeout=10, headers=headers)
            return response.url
        return url
    except Exception as e:
        return url

def generate_shopee_link(origin_url):
    try:
        timestamp = int(time.time())
        endpoint = "https://open-api.affiliate.shopee.vn/graphql"
        real_url = get_original_url(origin_url)
        
        # CẤU TRÚC QUERY ĐƠN GIẢN HÓA (TRUYỀN TRỰC TIẾP GIÁ TRỊ)
        # Cách này giúp tránh lỗi khai báo biến Mutation
        query = """
        mutation {
            generateShortLink(input: {
                originUrl: "%s", 
                externalTransactionId: "toolaff"
            }) {
                shortLink
            }
        }
        """ % real_url

        body = json.dumps({'query': query})
        
        base_str = APP_ID + str(timestamp) + body + APP_SECRET
        signature = hashlib.sha256(base_str.encode('utf-8')).hexdigest()

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"SHA256 Credential={APP_ID}, Signature={signature}, Timestamp={timestamp}"
        }

        response = requests.post(endpoint, headers=headers, data=body, timeout=15)
        res_data = response.json()
        
        print(f"Shopee Response: {res_data}")
        
        if 'data' in res_data and res_data['data'] and res_data['data'].get('generateShortLink'):
            return res_data['data']['generateShortLink']['shortLink']
        return None
    except Exception as e:
        print(f"Lỗi API Shopee: {e}")
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
        # Nếu lỗi, trả về cả thông báo lỗi chi tiết để mình dễ sửa
        return jsonify({"error": "API Shopee từ chối link. Hãy thử lại sau ít phút."})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)