import os
import json
import hashlib
import time
import random
import requests

# GitHub Secrets থেকে API Credentials নেওয়া হচ্ছে
APP_KEY = os.environ.get("ALI_APP_KEY")
APP_SECRET = os.environ.get("ALI_APP_SECRET")

def generate_sign(params, secret):
    """AliExpress API Sign জেনারেট করার স্ট্যান্ডার্ড মেথড"""
    sorted_params = sorted(params.items())
    query = secret + "".join([f"{k}{v}" for k, v in sorted_params]) + secret
    return hashlib.md5(query.encode("utf-8")).hexdigest().upper()

def parse_product_item(item):
    """এপিআই থেকে আসা পণ্যগুলোর ডেটা গুছিয়ে স্ট্যান্ডার্ড ফরম্যাট তৈরি করা"""
    return {
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

def fetch_aliexpress_data():
    if not APP_KEY or not APP_SECRET:
        print("API Keys are missing!")
        return

    url = "https://api-sg.aliexpress.com/sync"
    os.makedirs("aliexpress", exist_ok=True)

    # ==========================================
    # 1. Fetching Hot Products for Homepage (products.json)
    # ==========================================
    print("Fetching hot/trending products for homepage...")
    timestamp = str(int(time.time() * 1000))
    
    # হট প্রোডাক্টের জন্য পেজ রেঞ্জ বাড়িয়ে ১ থেকে ১০ এর মধ্যে র‍্যান্ডম করা হলো
    random_hot_page = str(random.randint(1, 10))
    
    hot_params = {
        'app_key': APP_KEY,
        'timestamp': timestamp,
        'sign_method': 'md5',
        'method': 'aliexpress.affiliate.hotproduct.query',
        'format': 'json',
        'v': '2.0',
        'page_no': random_hot_page,
        'page_size': '30'
    }
    hot_params['sign'] = generate_sign(hot_params, APP_SECRET)
    
    try:
        response = requests.get(url, params=hot_params)
        data = response.json()
        hot_products = []
        response_key = 'aliexpress_affiliate_hotproduct_query_response'
        
        if response_key in data and 'resp_result' in data[response_key]:
            resp_result = data[response_key]['resp_result']
            raw_products = resp_result.get('result', {}).get('products', [])
            if isinstance(raw_products, dict) and 'product' in raw_products:
                raw_products = raw_products['product']
            
            if isinstance(raw_products, list):
                for item in raw_products:
                    p_data = parse_product_item(item)
                    if p_data["title"] and p_data["image"]:
                        hot_products.append(p_data)
                        
        if hot_products:
            with open("aliexpress/products.json", "w", encoding="utf-8") as f:
                json.dump(hot_products, f, ensure_ascii=False, indent=4)
            print(f"Successfully saved {len(hot_products)} products to products.json (Page: {random_hot_page})")
    except Exception as e:
        print(f"Error fetching hot products: {e}")

    time.sleep(1)

    # ==========================================
    # 2. Fetching Category Products (products_category.json)
    # ==========================================
    print("Fetching category-based products for category pages...")
    
    # আপনার মেনুবারের নির্দিষ্ট ক্যাটাগরি কিওয়ার্ডগুলো
    menu_keywords = ["Fashion", "Electronics", "Gadgets", "Lifestyle", "Food", "Beauty", "Sports", "Accessories", "Offers", "Deals"]
    
    # অতিরিক্ত ট্রেন্ডিং ও সার্চ কিওয়ার্ডের বিশাল লিস্ট (যাতে কোড বারবার এডিট করতে না হয়)
    extra_trending_keywords = [
        "Smart Watch", "Wireless Earbuds", "Phone Case", "LED Lights", "Mini Fan",
        "Kitchen Gadgets", "Makeup Brushes", "Men Wallet", "Backpack", "Sunglasses",
        "Home Decor", "Fitness Band", "Bluetooth Speaker", "Car Accessories", "Toys",
        "Shoes", "Necklace", "Ring", "Hair Dryer", "Nail Art", "Portable Charger",
        "Gaming Mouse", "Mechanical Keyboard", "Laptop Stand", "Water Bottle",
        "Yoga Mat", "Resistance Bands", "Smart Bulb", "Security Camera", "Pet Toys",
        "Running Shoes", "Mens Jacket", "Womens Dress", "Crossbody Bag", "Smart Ring",
        "Tablet Stand", "Car Phone Holder", "Desk Lamp", "Mini Projector", "Air Purifier"
    ]

    # সব কিওয়ার্ড একসাথে করে অটোমেটিক শাফেল করা হবে
    all_keywords = list(set(menu_keywords + extra_trending_keywords))
    
    # প্রতিবার রান করার সময় এখান থেকে র‍্যান্ডমলি ১৫ থেকে ২৫টি কিওয়ার্ড অটো পিক করবে
    selected_keywords = random.sample(all_keywords, min(22, len(all_keywords)))

    category_products = []
    seen_ids = set()

    for keyword in selected_keywords:
        # পেজ নম্বর সম্পূর্ণ র‍্যান্ডম করা হলো (১ থেকে ২০ এর মধ্যে যেকোনো পেজ থেকে ডেটা আনবে)
        random_page = str(random.randint(1, 20))
        timestamp = str(int(time.time() * 1000))
        
        cat_params = {
            'app_key': APP_KEY,
            'timestamp': timestamp,
            'sign_method': 'md5',
            'method': 'aliexpress.affiliate.product.query',
            'format': 'json',
            'v': '2.0',
            'keywords': keyword,
            'page_no': random_page,
            'page_size': '25',
            'target_currency': 'USD'
        }
        cat_params['sign'] = generate_sign(cat_params, APP_SECRET)
        
        try:
            response = requests.get(url, params=cat_params)
            data = response.json()
            response_key = 'aliexpress_affiliate_product_query_response'
            
            if response_key in data and 'resp_result' in data[response_key]:
                resp_result = data[response_key]['resp_result']
                raw_products = resp_result.get('result', {}).get('products', [])
                if isinstance(raw_products, dict) and 'product' in raw_products:
                    raw_products = raw_products['product']
                
                if isinstance(raw_products, list):
                    for item in raw_products:
                        prod_id = item.get("product_id")
                        if prod_id in seen_ids:
                            continue
                        seen_ids.add(prod_id)

                        p_data = parse_product_item(item)
                        p_data["search_keyword"] = keyword

                        # ডিফল্ট নাম বাদ দিয়ে এপিআই থেকে আসা ক্যাটাগরি বা কিওয়ার্ড ব্যবহার করা হয়েছে
                        if not p_data["second_category_name"]:
                            p_data["second_category_name"] = keyword
                        if not p_data["first_category_name"]:
                            p_data["first_category_name"] = keyword

                        if p_data["title"] and p_data["image"]:
                            category_products.append(p_data)
        except Exception as e:
            print(f"Error fetching for keyword '{keyword}': {e}")
        
        time.sleep(1)

    if category_products:
        with open("aliexpress/products_category.json", "w", encoding="utf-8") as f:
            json.dump(category_products, f, ensure_ascii=False, indent=4)
        print(f"Successfully saved {len(category_products)} unique products to products_category.json")

if __name__ == "__main__":
    fetch_aliexpress_data()
