import os
import json
import hashlib
import time
import requests

# GitHub Secrets থেকে API Credentials নেওয়া হচ্ছে
APP_KEY = os.environ.get("ALI_APP_KEY")
APP_SECRET = os.environ.get("ALI_APP_SECRET")

def generate_sign(params, secret):
    """AliExpress API Sign জেনারেট করার স্ট্যান্ডার্ড মেথড"""
    sorted_params = sorted(params.items())
    query = secret + "".join([f"{k}{v}" for k, v in sorted_params]) + secret
    return hashlib.md5(query.encode("utf-8")).hexdigest().upper()

def fetch_aliexpress_products():
    if not APP_KEY or not APP_SECRET:
        print("API Keys are missing!")
        return

    print("Fetching hot/trending products from AliExpress API...")
    
    url = "https://api-sg.aliexpress.com/sync"
    timestamp = str(int(time.time() * 1000))
    
    params = {
        'app_key': APP_KEY,
        'timestamp': timestamp,
        'sign_method': 'md5',
        'method': 'aliexpress.affiliate.hotproduct.query', 
        'format': 'json',
        'v': '2.0',
        'page_no': '1',
        'page_size': '20'
    }
    
    # সিগনেচার জেনারেট করা
    params['sign'] = generate_sign(params, APP_SECRET)
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        # এপিআই থেকে আসা সম্পূর্ণ রেসপন্সটি লগে প্রিন্ট করা
        print("API Full Response:", json.dumps(data, indent=2))
        
        products = []
        response_key = 'aliexpress_affiliate_hotproduct_query_response'
        
        if response_key in data and 'resp_result' in data[response_key]:
            resp_result = data[response_key]['resp_result']
            
            # আলিবাবা এপিআই রেসপন্সের বিভিন্ন স্ট্রাকচার হ্যান্ডেল করার নিরাপদ উপায়
            raw_products = []
            if 'result' in resp_result and 'products' in resp_result['result']:
                raw_products = resp_result['result']['products']
                if isinstance(raw_products, dict) and 'product' in raw_products:
                    raw_products = raw_products['product']
            
            if isinstance(raw_products, list):
                for item in raw_products:
                    title = item.get("product_title")
                    price = item.get("target_sale_price") or item.get("sale_price") or "0.00"
                    image = item.get("product_main_image_url")
                    affiliate_link = item.get("promotion_link") or item.get("product_detail_url")
                    
                    if title and image:
                        products.append({
                            "title": title,
                            "price": f"${price}",
                            "image": image,
                            "affiliate_link": affiliate_link
                        })
        
        if not products:
            print("Warning: No products retrieved from API or check API permission status.")
            return

        # ফোল্ডার নিশ্চিত করা
        os.makedirs("aliexpress", exist_ok=True)

        # products.json ফাইলে সেভ করা
        with open("aliexpress/products.json", "w", encoding="utf-8") as f:
            json.dump(products, f, ensure_ascii=False, indent=4)
            
        print(f"Successfully fetched and saved {len(products)} products dynamically!")

    except Exception as e:
        print(f"Error fetching from AliExpress API: {e}")

if __name__ == "__main__":
    fetch_aliexpress_products()
