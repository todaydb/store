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

    print("Fetching hot/trending products from AliExpress API with all details...")
    
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
        'page_size': '20' # আপনি চাইলে এখানে বাড়িয়ে নিতে পারেন (সর্বোচ্চ ৫০)
    }
    
    # সিগনেচার জেনারেট করা
    params['sign'] = generate_sign(params, APP_SECRET)
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        products = []
        response_key = 'aliexpress_affiliate_hotproduct_query_response'
        
        if response_key in data and 'resp_result' in data[response_key]:
            resp_result = data[response_key]['resp_result']
            
            raw_products = []
            if 'result' in resp_result and 'products' in resp_result['result']:
                raw_products = resp_result['result']['products']
                if isinstance(raw_products, dict) and 'product' in raw_products:
                    raw_products = raw_products['product']
            
            if isinstance(raw_products, list):
                for item in raw_products:
                    # এপিআই থেকে আসা সমস্ত প্রয়োজনীয় ফিল্ড একটি ডিকশনারিতে গুছিয়ে নেওয়া হচ্ছে
                    product_data = {
                        "product_id": item.get("product_id"),
                        "title": item.get("product_title", ""),
                        "sale_price": item.get("target_sale_price") or item.get("sale_price") or "0.00",
                        "sale_price_currency": item.get("target_sale_price_currency") or item.get("sale_price_currency", "USD"),
                        "original_price": item.get("target_original_price") or item.get("original_price") or "",
                        "original_price_currency": item.get("target_original_price_currency") or item.get("original_price_currency", "USD"),
                        "app_sale_price": item.get("target_app_sale_price") or item.get("app_sale_price") or "",
                        "discount": item.get("discount", ""),
                        "commission_rate": item.get("commission_rate", ""),
                        "hot_product_commission_rate": item.get("hot_product_commission_rate", ""),
                        "evaluate_rate": item.get("evaluate_rate", ""),
                        "sales_volume": item.get("lastest_volume", 0),
                        "image": item.get("product_main_image_url", ""),
                        "small_images": item.get("product_small_image_urls", {}).get("string", []) if isinstance(item.get("product_small_image_urls"), dict) else item.get("product_small_image_urls", []),
                        "video_url": item.get("product_video_url", ""),
                        "affiliate_link": item.get("promotion_link") or item.get("product_detail_url", ""),
                        "product_detail_url": item.get("product_detail_url", ""),
                        "promotion_link": item.get("promotion_link", ""),
                        "first_category_id": item.get("first_level_category_id", ""),
                        "first_category_name": item.get("first_level_category_name", ""),
                        "second_category_id": item.get("second_level_category_id", ""),
                        "second_category_name": item.get("second_level_category_name", ""),
                        "shop_id": item.get("shop_id", ""),
                        "shop_name": item.get("shop_name", ""),
                        "shop_url": item.get("shop_url", ""),
                        "tax_rate": item.get("tax_rate", "0.00"),
                        "ship_to_days": item.get("ship_to_days", ""),
                        "promo_code_info": item.get("promo_code_info", {})
                    }
                    
                    if product_data["title"] and product_data["image"]:
                        products.append(product_data)
        
        if not products:
            print("Warning: No products retrieved from API.")
            return

        # ফোল্ডার নিশ্চিত করা
        os.makedirs("aliexpress", exist_ok=True)

        # products.json ফাইলে সমস্ত তথ্য সেভ করা
        with open("aliexpress/products.json", "w", encoding="utf-8") as f:
            json.dump(products, f, ensure_ascii=False, indent=4)
            
        print(f"Successfully saved {len(products)} products with ALL API fields to products.json!")

    except Exception as e:
        print(f"Error fetching from AliExpress API: {e}")

if __name__ == "__main__":
    fetch_aliexpress_products()
