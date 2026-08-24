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
    
    # এখানে আমরা ট্রেন্ডিং বা হট প্রোডাক্ট এপিআই মেথড ব্যবহার করছি, 
    # যাতে নির্দিষ্ট কোনো কিওয়ার্ড ছাড়াই সেরা প্রোডাক্টগুলো সিরিয়ালি চলে আসে।
    params = {
        'app_key': APP_KEY,
        'timestamp': timestamp,
        'sign_method': 'md5',
        'method': 'aliexpress.affiliate.hotproduct.query', 
        'format': 'json',
        'v': '2.0',
        'page_no': '1',
        'page_size': '20' # আপনি একসাথে কয়টি প্রোডাক্ট আনতে চান (যেমন ২০টি)
    }
    
    # সিগনেচার জেনারেট করা
    params['sign'] = generate_sign(params, APP_SECRET)
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        # এপিআই থেকে আসা সম্পূর্ণ রেসপন্সটি লগে প্রিন্ট করে দেখার জন্য (ডিবাগিং)
        print("API Full Response:", json.dumps(data, indent=2))
        
        products = []
        
        # AliExpress Hot Product API রেসপন্স স্ট্রাকচার পার্স করা
        response_key = 'aliexpress_affiliate_hotproduct_query_response'
        
        if response_key in data and 'resp_result' in data[response_key]:
            result = data[response_key]['resp_result']
            if 'result' in result and 'products' in result['result']:
                raw_products = result['result']['products']
                
                for item in raw_products:
                    # এপিআই থেকে সরাসরি পাওয়া রিয়েল ডাটা ম্যাপিং
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
        
        # যদি কোনো কারণে এপিআই রেসপন্স ফাকা থাকে
        if not products:
            print("Warning: No products retrieved from API or check API permission status.")
            return

        # ফোল্ডার নিশ্চিত করা
        os.makedirs("aliexpress", exist_ok=True)

        # ডাইনামিক প্রোডাক্টগুলো products.json ফাইলে সেভ করা হচ্ছে
        with open("aliexpress/products.json", "w", encoding="utf-8") as f:
            json.dump(products, f, ensure_ascii=False, indent=4)
            
        print(f"Successfully fetched and saved {len(products)} products dynamically!")

    except Exception as e:
        print(f"Error fetching from AliExpress API: {e}")

if __name__ == "__main__":
    fetch_aliexpress_products()
