#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DMMブックス データ取得スクリプト（成人向け含む）
- 一般向け: 少女・女性マンガ、TL、BL、文芸・ラノベ
- 成人向け: アダルトマンガ、官能小説、写真集、成人BL、成人TL
各カテゴリのTOP10を取得してJSONに保存
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

def fetch_books_ranking(site='DMM.com', service='book', floor='book', keyword=None, hits=10):
    """DMMブックスのランキングを取得"""
    params = {
        'api_id': API_ID,
        'affiliate_id': AFFILIATE_ID,
        'site': site,
        'service': service,
        'floor': floor,
        'hits': hits,
        'sort': 'rank',
        'output': 'json'
    }
    
    if keyword:
        params['keyword'] = keyword
    
    try:
        print(f"🔄 Fetching {keyword or floor} (site={site})...")
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
    
    all_data = {
        'updated_at': datetime.now().isoformat(),
        'general_categories': {},  # 一般向け
        'adult_categories': {}      # 成人向け
    }
    
    # 一般向けカテゴリ（FANZAのブックスから取得）
    print("\n📚 === 一般向けカテゴリ ===")
    general_categories = {
        'girls_comics': {'floor': 'comic', 'name': '少女・女性マンガ'},
        'tl': {'floor': 'tl', 'name': 'TL（ティーンズラブ）'},
        'bl': {'floor': 'bl', 'name': 'BL（ボーイズラブ）'},
        'novels': {'floor': 'novel', 'name': '文芸・ラノベ'}
    }
    
    for category_id, config in general_categories.items():
        print(f"\n📖 {config['name']}")
        items = fetch_books_ranking(
            site='FANZA',
            service='book',
            floor=config['floor'],
            hits=10
        )
        all_data['general_categories'][category_id] = {
            'name': config['name'],
            'items': items
        }
        time.sleep(2)
    
    # 成人向けカテゴリ
    print("\n🔞 === 成人向けカテゴリ ===")
    adult_categories = {
        'adult_manga': {'floor': 'comic', 'name': 'アダルトマンガ'},
        'adult_novel': {'floor': 'novel', 'name': '美少女ノベル・官能小説'},
        'adult_photo': {'floor': 'photo', 'name': 'アダルト写真集・雑誌'},
        'adult_bl': {'floor': 'bl', 'name': '成人向けBL'},
        'adult_tl': {'floor': 'tl', 'name': '成人向けTL'}
    }
    
    for category_id, config in adult_categories.items():
        print(f"\n🔞 {config['name']}")
        items = fetch_books_ranking(
            site='FANZA',
            service='book',
            floor=config['floor'],
            hits=10
        )
        all_data['adult_categories'][category_id] = {
            'name': config['name'],
            'items': items
        }
        time.sleep(2)
    
    # JSONファイルに保存
    import os
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Data saved to {OUTPUT_FILE}")
    print(f"\n📊 Summary:")
    print(f"  一般向け: {len(all_data['general_categories'])} categories")
    for cat_data in all_data['general_categories'].values():
        print(f"    - {cat_data['name']}: {len(cat_data['items'])} items")
    
    print(f"\n  成人向け: {len(all_data['adult_categories'])} categories")
    for cat_data in all_data['adult_categories'].values():
        print(f"    - {cat_data['name']}: {len(cat_data['items'])} items")
    
    print(f"\n🎉 Completed at {datetime.now()}")

if __name__ == "__main__":
    main()
