#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DMMブックス データ取得スクリプト（修正版）
各ジャンルを個別に取得して重複を防止
"""

import requests
import json
from datetime import datetime
import time
import os

# API設定
API_ID = os.environ.get('FANZA_API_ID', 'a2BXCsL2MVUtUeuFBZ1h')
AFFILIATE_ID = os.environ.get('FANZA_AFFILIATE_ID', 'yoru365-990')
BASE_URL = 'https://api.dmm.com/affiliate/v3/ItemList'

# 出力ファイル
OUTPUT_FILE = 'data/books_data.json'

def fetch_books_by_genre(site, floor_code, genre_id=None, hits=10):
    """ジャンル指定でブックスを取得"""
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
    
    # ジャンル指定がある場合
    if genre_id:
        params['article'] = 'genre'
        params['article_id'] = genre_id
    
    try:
        print(f"🔄 Fetching {site} / {floor_code} / genre:{genre_id or 'all'}...")
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
    
    # 少女・女性マンガ（ジャンルID: 66033, 66034）
    print("\n📖 少女・女性マンガ")
    girls_comics = fetch_books_by_genre('DMM.com', 'comic', genre_id=66033, hits=10)
    time.sleep(1)
    
    # TL（ジャンルID: 66060）
    print("\n💕 TL")
    tl_comics = fetch_books_by_genre('DMM.com', 'comic', genre_id=66060, hits=10)
    time.sleep(1)
    
    # BL（ジャンルID: 66036）
    print("\n💙 BL")
    bl_comics = fetch_books_by_genre('DMM.com', 'comic', genre_id=66036, hits=10)
    time.sleep(1)
    
    # 文芸・ラノベ（ジャンルID: 66041）
    print("\n📚 文芸・ラノベ")
    novels = fetch_books_by_genre('DMM.com', 'novel', genre_id=66041, hits=10)
    time.sleep(1)
    
    all_data['general_categories'] = {
        'girls_comics': {'name': '少女・女性マンガ', 'items': girls_comics},
        'tl': {'name': 'TL（ティーンズラブ）', 'items': tl_comics},
        'bl': {'name': 'BL（ボーイズラブ）', 'items': bl_comics},
        'novels': {'name': '文芸・ラノベ', 'items': novels}
    }
    
    # 成人向けカテゴリ（FANZA）
    print("\n🔞 === 成人向けカテゴリ (FANZA) ===")
    
    # アダルトマンガ
    print("\n📕 アダルトマンガ")
    adult_comic = fetch_books_by_genre('FANZA', 'comic', hits=10)
    time.sleep(1)
    
    # 官能小説
    print("\n📘 官能小説")
    adult_novel = fetch_books_by_genre('FANZA', 'novel', hits=10)
    time.sleep(1)
    
    # 写真集
    print("\n📷 写真集")
    adult_photo = fetch_books_by_genre('FANZA', 'photo', hits=10)
    time.sleep(1)
    
    # 成人向けBL
    print("\n💙 成人向けBL")
    adult_bl = fetch_books_by_genre('FANZA', 'comic', genre_id=66042, hits=10)
    time.sleep(1)
    
    # 成人向けTL
    print("\n💕 成人向けTL")
    adult_tl = fetch_books_by_genre('FANZA', 'comic', genre_id=66064, hits=10)
    time.sleep(1)
    
    all_data['adult_categories'] = {
        'adult_manga': {'name': 'アダルトマンガ', 'items': adult_comic},
        'adult_novel': {'name': '美少女ノベル・官能小説', 'items': adult_novel},
        'adult_photo': {'name': 'アダルト写真集・雑誌', 'items': adult_photo},
        'adult_bl': {'name': '成人向けBL', 'items': adult_bl},
        'adult_tl': {'name': '成人向けTL', 'items': adult_tl}
    }
    
    # JSONファイルに保存
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Data saved to {OUTPUT_FILE}")
    print(f"\n📊 Summary:")
    print(f"  少女・女性マンガ: {len(girls_comics)} items")
    print(f"  TL: {len(tl_comics)} items")
    print(f"  BL: {len(bl_comics)} items")
    print(f"  文芸・ラノベ: {len(novels)} items")
    print(f"  アダルトマンガ: {len(adult_comic)} items")
    print(f"  官能小説: {len(adult_novel)} items")
    print(f"  写真集: {len(adult_photo)} items")
    print(f"  成人向けBL: {len(adult_bl)} items")
    print(f"  成人向けTL: {len(adult_tl)} items")
    print(f"\n🎉 Completed at {datetime.now()}")

if __name__ == "__main__":
    main()
