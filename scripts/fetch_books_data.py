#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DMMブックス データ取得スクリプト（シンプル版）
全カテゴリFANZAサイトから取得
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

def fetch_books_simple(hits=10):
    """シンプルにFANZAブックスランキングを取得"""
    params = {
        'api_id': API_ID,
        'affiliate_id': AFFILIATE_ID,
        'site': 'FANZA',
        'service': 'book',
        'hits': hits,
        'sort': 'rank',
        'output': 'json'
    }
    
    try:
        print(f"🔄 Fetching FANZA books ranking...")
        response = requests.get(BASE_URL, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if 'result' in data and 'items' in data['result']:
            items = data['result']['items']
            # noimage を除外
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
    
    # シンプルに全カテゴリ同じデータを使用（TOP10）
    books = fetch_books_simple(hits=10)
    
    all_data = {
        'updated_at': datetime.now().isoformat(),
        'general_categories': {
            'girls_comics': {'name': '少女・女性マンガ', 'items': books},
            'tl': {'name': 'TL（ティーンズラブ）', 'items': books},
            'bl': {'name': 'BL（ボーイズラブ）', 'items': books},
            'novels': {'name': '文芸・ラノベ', 'items': books}
        },
        'adult_categories': {
            'adult_manga': {'name': 'アダルトマンガ', 'items': books},
            'adult_novel': {'name': '美少女ノベル・官能小説', 'items': books},
            'adult_photo': {'name': 'アダルト写真集・雑誌', 'items': books},
            'adult_bl': {'name': '成人向けBL', 'items': books},
            'adult_tl': {'name': '成人向けTL', 'items': books}
        }
    }
    
    # JSONファイルに保存
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Data saved to {OUTPUT_FILE}")
    print(f"📊 Total items: {len(books)}")
    print(f"\n🎉 Completed at {datetime.now()}")

if __name__ == "__main__":
    main()
