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
    """Xử lý các link rút gọn của Shopee để lấy link gốc trước khi convert"""
    try:
        if "s.shopee.vn" in url or "shope.ee" in url or "shopee.vn" in url:
            # Sử dụng headers để giả lập trình duyệt, tránh bị Shopee chặn
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.head(url, allow_redirects=True, timeout=10, headers=headers)
            return response.url
        return url
    except Exception as e:
        print(f"Lỗi lấy link gốc: {e}")
        return url

def generate_shopee_link(origin_url):
    try:
        timestamp = int(time.time())
        endpoint = "https://open-api.affiliate.shopee.vn/graphql"
        
        real_url = get_original_url(origin_url)
        
        # Cấu hình Query chuẩn theo tài liệu Shopee Affiliate
        query = """
        mutation($url: String!) {
            generateShortLink(input: {originUrl: $url}) {
                shortLink
            }
        }
        """
        variables = {"url": real_url}
        body = json.dumps({'query': query, 'variables': variables})
        
        # Tạo chữ ký bảo mật SHA256
        base_str = APP_ID + str(timestamp) + body + APP_SECRET
        signature = hashlib.sha256(base_str.encode('utf-8')).hexdigest()

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"SHA256 Credential={APP_ID}, Signature={signature}, Timestamp={timestamp}"
        }

        response = requests.post(endpoint, headers=headers, data=body, timeout=15)
        res_data = response.json()
        
        # Log kết quả để kiểm tra trong phần Logs của Render
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
        return jsonify({"error": "Không thể chuyển đổi link này. Hãy kiểm tra lại link Shopee của bạn."})

if __name__ == '__main__':
    # Cấu hình quan trọng để chạy được trên Render
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)