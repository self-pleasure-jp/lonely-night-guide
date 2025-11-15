#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DMMブックス 自動ツイート投稿スクリプト
- JSONから順番に投稿
- 画像付き（ぼかしなし）
- センシティブ設定
"""

import os
import json
import tweepy
from datetime import datetime
import requests
from io import BytesIO
from PIL import Image

# 環境変数から認証情報を取得
TWITTER_API_KEY = os.environ.get('TWITTER_API_KEY')
TWITTER_API_SECRET = os.environ.get('TWITTER_API_SECRET')
TWITTER_ACCESS_TOKEN = os.environ.get('TWITTER_ACCESS_TOKEN')
TWITTER_ACCESS_TOKEN_SECRET = os.environ.get('TWITTER_ACCESS_TOKEN_SECRET')

COUNTER_FILE = 'data/counter.txt'
DATA_FILE = 'data/books_data.json'

def load_books_data():
    """JSONデータを読み込み"""
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            print(f"✅ Loaded data from {DATA_FILE}")
            return data
    except FileNotFoundError:
        print(f"❌ Error: {DATA_FILE} not found")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error: {e}")
        return None

def get_current_counter():
    """現在のカウンターを取得"""
    try:
        with open(COUNTER_FILE, 'r') as f:
            counter = int(f.read().strip())
            print(f"📊 Current counter: {counter}")
            return counter
    except FileNotFoundError:
        print("📊 Counter file not found, starting from 0")
        return 0
    except ValueError:
        print("⚠️ Invalid counter value, resetting to 0")
        return 0

def save_counter(counter):
    """カウンターを保存"""
    os.makedirs(os.path.dirname(COUNTER_FILE), exist_ok=True)
    with open(COUNTER_FILE, 'w') as f:
        f.write(str(counter))
    print(f"💾 Saved counter: {counter}")

def build_all_items_list(data):
    """全アイテムをフラットなリストに変換"""
    all_items = []
    
    # 一般向けカテゴリ
    for category_id, category_data in data.get('general_categories', {}).items():
        for item in category_data.get('items', []):
            all_items.append({
                'type': 'general',
                'category_id': category_id,
                'category_name': category_data['name'],
                'item': item
            })
    
    # 成人向けカテゴリ
    for category_id, category_data in data.get('adult_categories', {}).items():
        for item in category_data.get('items', []):
            all_items.append({
                'type': 'adult',
                'category_id': category_id,
                'category_name': category_data['name'],
                'item': item
            })
    
    print(f"📋 Total items: {len(all_items)}")
    return all_items

def select_item_by_counter(all_items, counter):
    """カウンターに基づいてアイテムを選択"""
    if not all_items:
        return None
    
    index = counter % len(all_items)
    selected = all_items[index]
    
    print(f"🎯 Selected item {index + 1}/{len(all_items)}: {selected['category_name']}")
    return selected

def download_image(image_url):
    """画像をダウンロード（ぼかしなし）"""
    try:
        print(f"🖼️  Downloading image from: {image_url}")
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()
        
        # 画像を開く
        image = Image.open(BytesIO(response.content))
        print(f"✅ Image downloaded: {image.size}")
        
        # メモリ上のバイトストリームに保存
        output = BytesIO()
        image.save(output, format='JPEG', quality=85)
        output.seek(0)
        
        return output
        
    except Exception as e:
        print(f"❌ Error processing image: {e}")
        return None

def create_tweet_text(selected):
    """投稿テキストを生成"""
    item = selected['item']
    category_name = selected['category_name']
    item_type = selected['type']
    
    title = item.get('title', 'タイトル不明')
    url = item.get('affiliateURL', item.get('URL', ''))
    
    # タイトルを70文字に制限
    if len(title) > 70:
        title = title[:67] + '...'
    
    # シンプルな投稿
    tweet = f"{category_name}\n\n{title}\n\n{url}"
    
    return tweet

def create_fallback_tweet():
    """フォールバックツイート"""
    return """DMMブックスで心満たされる一冊を

恋愛マンガ、BL、TL、ラノベなど
今夜を優しく満たす作品が見つかります

https://al.dmm.com/?lurl=https%3A%2F%2Fbook.dmm.com%2F&af_id=yoru365-990&ch=link_tool&ch_id=link"""

def post_tweet_with_image(tweet_text, image_data):
    """画像付きツイートを投稿"""
    try:
        # API v1.1 for media upload
        auth = tweepy.OAuth1UserHandler(
            TWITTER_API_KEY,
            TWITTER_API_SECRET,
            TWITTER_ACCESS_TOKEN,
            TWITTER_ACCESS_TOKEN_SECRET
        )
        api = tweepy.API(auth)
        
        # 画像をアップロード
        if image_data:
            print("📤 Uploading image...")
            media = api.media_upload(filename="book_cover.jpg", file=image_data)
            media_id = media.media_id_string
            print(f"✅ Image uploaded: {media_id}")
            
            # センシティブ設定
            api.create_media_metadata(media_id, alt_text="書籍カバー")
        else:
            media_id = None
        
        # API v2 for tweet
        client = tweepy.Client(
            consumer_key=TWITTER_API_KEY,
            consumer_secret=TWITTER_API_SECRET,
            access_token=TWITTER_ACCESS_TOKEN,
            access_token_secret=TWITTER_ACCESS_TOKEN_SECRET
        )
        
        # ツイート投稿
        if media_id:
            response = client.create_tweet(text=tweet_text, media_ids=[media_id])
        else:
            response = client.create_tweet(text=tweet_text)
        
        print(f"✅ Tweet posted successfully! Tweet ID: {response.data['id']}")
        return True
        
    except tweepy.errors.Forbidden as e:
        print(f"❌ Forbidden error: {e}")
        print("⚠️ This might be a duplicate tweet")
        return False
    except Exception as e:
        print(f"❌ Error posting tweet: {e}")
        return False

def main():
    print(f"🚀 Starting DMM Books auto-post bot at {datetime.now()}")
    
    # データ読み込み
    data = load_books_data()
    if not data:
        print("⚠️ No data loaded, using fallback tweet")
        tweet_text = create_fallback_tweet()
        post_tweet_with_image(tweet_text, None)
        return
    
    # 全アイテムリスト作成
    all_items = build_all_items_list(data)
    if not all_items:
        print("⚠️ No items found, using fallback tweet")
        tweet_text = create_fallback_tweet()
        post_tweet_with_image(tweet_text, None)
        return
    
    # カウンター取得
    counter = get_current_counter()
    
    # アイテム選択
    selected = select_item_by_counter(all_items, counter)
    if not selected:
        print("⚠️ Could not select item, using fallback tweet")
        tweet_text = create_fallback_tweet()
        post_tweet_with_image(tweet_text, None)
        return
    
    # ツイート作成
    tweet_text = create_tweet_text(selected)
    
    # 画像取得
    item = selected['item']
    image_url = item.get('imageURL', {}).get('large') or item.get('imageURL', {}).get('small')
    
    image_data = None
    if image_url:
        image_data = download_image(image_url)
    else:
        print("⚠️ No image URL found")
    
    print("\n" + "="*50)
    print("📝 Tweet preview:")
    print("="*50)
    print(tweet_text)
    if image_data:
        print("\n🖼️  Image: Book cover attached")
    print("="*50 + "\n")
    
    # 投稿
    success = post_tweet_with_image(tweet_text, image_data)
    
    if success:
        new_counter = counter + 1
        save_counter(new_counter)
        print(f"✅ Counter updated: {counter} → {new_counter}")
    else:
        print("⚠️ Tweet failed, counter not updated")

if __name__ == "__main__":
    main()
