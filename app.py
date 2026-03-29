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
    """Lấy link gốc từ link rút gọn Shopee"""
    try:
        if any(domain in url for domain in ["s.shopee.vn", "shope.ee", "shopee.vn"]):
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, allow_redirects=True, timeout=10, headers=headers)
            return response.url
        return url
    except Exception as e:
        return url

def generate_shopee_link(origin_url):
    try:
        timestamp = int(time.time())
        endpoint = "https://open-api.affiliate.shopee.vn/graphql"
        real_url = get_original_url(origin_url)
        
        # CẤU TRÚC QUERY CHUẨN THEO ẢNH BẠN GỬI
        # subIds là một danh sách các chuỗi [String]
        query = """
        mutation($url: String!, $subIds: [String]) {
            generateShortLink(input: {originUrl: $url, subIds: $subIds}) {
                shortLink
            }
        }
        """
        
        variables = {
            "url": real_url,
            "subIds": ["toolaff"] # Truyền dạng danh sách theo đúng chuẩn [String]
        }
        
        body = json.dumps({'query': query, 'variables': variables})
        
        # Tạo chữ ký bảo mật
        base_str = APP_ID + str(timestamp) + body + APP_SECRET
        signature = hashlib.sha256(base_str.encode('utf-8')).hexdigest()

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"SHA256 Credential={APP_ID}, Signature={signature}, Timestamp={timestamp}"
        }

        response = requests.post(endpoint, headers=headers, data=body, timeout=15)
        res_data = response.json()
        
        # Log để kiểm tra nếu cần
        print(f"Shopee Response: {res_data}")
        
        if 'data' in res_data and res_data['data'] and res_data['data'].get('generateShortLink'):
            return res_data['data']['generateShortLink']['shortLink']
            
        return None
    except Exception as e:
        print(f"Lỗi hệ thống: {e}")
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
        return jsonify({"error": "Không thể tạo link. Vui lòng kiểm tra lại link Shopee hoặc thử lại sau."})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)