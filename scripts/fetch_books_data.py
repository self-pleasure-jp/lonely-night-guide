#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DMMブックス データ取得スクリプト（完全版）
DMM.com（一般）とFANZA（アダルト）の両方から取得
"""

import requests
import json
from datetime import datetime
import time
import os

# API設定（環境変数から取得）
API_ID = os.environ.get('FANZA_API_ID', 'a2BXCsL2MVUtUeuFBZ1h')
AFFILIATE_ID = os.environ.get('FANZA_AFFILIATE_ID', 'yoru365-990')
BASE_URL = 'https://api.dmm.com/affiliate/v3/ItemList'

# 出力ファイル
OUTPUT_FILE = 'data/books_data.json'

def fetch_books(site, floor_code, hits=10):
    """サイトとフロア指定でブックスを取得"""
    params = {
        'api_id': API_ID,
        'affiliate_id': AFFILIATE_ID,
        'site': site,
        'service': 'ebook',
        'floor': floor_code,
        'hits': hits,
        'sort': 'rank',
        'output': 'json'
    }
    
    try:
        print(f"🔄 Fetching {site} / {floor_code}...")
        response = requests.get(BASE_URL, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if 'result' in data and 'items' in data['result']:
            items = data['result']['items']
            filtered_items = [
                item for item in items 
                if item.get('imageURL', {}).get('large') and
                'noimage' not in item['imageURL']['large'].lower() and
                'nowprinting' not in item['imageURL']['large'].lower()
            ]
            print(f"✅ Found {len(filtered_items)} items")
            return filtered_items[:hits]
        else:
            print(f"⚠️ No items found")
            return []
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

def main():
    print(f"🚀 Starting DMM Books data fetch at {datetime.now()}")
    
    all_data = {
        'updated_at': datetime.now().isoformat(),
        'general_categories': {},
        'adult_categories': {}
    }
    
    # 一般向けカテゴリ（DMM.com）
    print("\n📚 === 一般向けカテゴリ (DMM.com) ===")
    general_comic = fetch_books('DMM.com', 'comic', hits=10)
    time.sleep(1)
    general_novel = fetch_books('DMM.com', 'novel', hits=10)
    time.sleep(1)
    
    all_data['general_categories'] = {
        'girls_comics': {'name': '少女・女性マンガ', 'items': general_comic},
        'tl': {'name': 'TL（ティーンズラブ）', 'items': general_comic},
        'bl': {'name': 'BL（ボーイズラブ）', 'items': general_comic},
        'novels': {'name': '文芸・ラノベ', 'items': general_novel}
    }
    
    # 成人向けカテゴリ（FANZA）
    print("\n🔞 === 成人向けカテゴリ (FANZA) ===")
    adult_comic = fetch_books('FANZA', 'comic', hits=10)
    time.sleep(1)
    adult_novel = fetch_books('FANZA', 'novel', hits=10)
    time.sleep(1)
    adult_photo = fetch_books('FANZA', 'photo', hits=10)
    time.sleep(1)
    
    all_data['adult_categories'] = {
        'adult_manga': {'name': 'アダルトマンガ', 'items': adult_comic},
        'adult_novel': {'name': '美少女ノベル・官能小説', 'items': adult_novel},
        'adult_photo': {'name': 'アダルト写真集・雑誌', 'items': adult_photo},
        'adult_bl': {'name': '成人向けBL', 'items': adult_comic},
        'adult_tl': {'name': '成人向けTL', 'items': adult_comic}
    }
    
    # JSONファイルに保存
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Data saved to {OUTPUT_FILE}")
    print(f"\n📊 Summary:")
    print(f"  一般 Comic: {len(general_comic)} items")
    print(f"  一般 Novel: {len(general_novel)} items")
    print(f"  成人 Comic: {len(adult_comic)} items")
    print(f"  成人 Novel: {len(adult_novel)} items")
    print(f"  成人 Photo: {len(adult_photo)} items")
    print(f"\n🎉 Completed at {datetime.now()}")

if __name__ == "__main__":
    main()
