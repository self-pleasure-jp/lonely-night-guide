#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DMMブックス 自動ツイート投稿スクリプト（成人向けぼかし版）
- 一般向け: 画像そのまま
- 成人向け: 画像ぼかし＋テキスト伏字
"""

import os
import json
import tweepy
from datetime import datetime
import requests
from io import BytesIO
from PIL import Image, ImageFilter

# 環境変数から認証情報を取得
TWITTER_API_KEY = os.environ.get('TWITTER_API_KEY')
TWITTER_API_SECRET = os.environ.get('TWITTER_API_SECRET')
TWITTER_ACCESS_TOKEN = os.environ.get('TWITTER_ACCESS_TOKEN')
TWITTER_ACCESS_TOKEN_SECRET = os.environ.get('TWITTER_ACCESS_TOKEN_SECRET')

COUNTER_FILE = 'data/counter.txt'
DATA_FILE = 'data/books_data.json'

# 成人向けカテゴリID
ADULT_CATEGORIES = ['adult_manga', 'adult_novel', 'adult_photo', 'adult_bl', 'adult_tl']

# ジャンル別コメントテンプレート（より深い感想）
GENRE_COMMENTS = {
    'girl_comic': [
        'キャラの心情描写が丁寧で、読んでいて自然と感情移入してしまう。恋の駆け引きにドキドキが止まらない',
        'ストーリー展開が予測不能で、次が気になって一気読み。登場人物の成長が見ていて心地よい',
        '切ないシーンでは涙腺が緩み、幸せなシーンでは心が温かくなる。王道の恋愛ストーリーだけど飽きない',
        '主人公の葛藤がリアルで共感できる。読み終わった後もしばらく余韻に浸ってしまう作品'
    ],
    'tl': [
        '大人の恋愛の機微が繊細に描かれていて、ページをめくる手が止まらない。甘いだけじゃない深みがある',
        'リアルな恋愛の駆け引きが面白い。仕事と恋のバランス、誰もが共感できる悩みが詰まっている',
        '官能的なシーンも品があり、ストーリーとして成立している。夜にゆっくり読みたくなる作品',
        'キャラクターの心理描写が巧みで、読んでいて感情が揺さぶられる。大人だからこその切なさが胸に響く'
    ],
    'bl': [
        '繊細な感情の揺れ動きが丁寧に描かれていて、二人の関係性に引き込まれる。心理描写が本当に秀逸',
        '美しい世界観と深いストーリーに心を奪われる。読後は余韻が長く残る、そんな作品',
        'キャラクターの内面が丁寧に掘り下げられていて、感情移入せずにはいられない。泣けるシーンも多い',
        '恋愛だけでなく、生き方や価値観についても考えさせられる。読み応えのある一冊'
    ],
    'novel': [
        '文章の美しさに惹き込まれ、気づけば物語の世界に没入している。読後感が素晴らしい名作',
        '登場人物の心情が丁寧に描かれていて、まるで自分がその場にいるような臨場感。ページをめくる手が止まらない',
        'ストーリーの構成が見事で、伏線回収の快感がたまらない。何度も読み返したくなる深みがある',
        '人間の本質や生き方について深く考えさせられる。心に長く残る、そんな作品'
    ],
    'adult_manga': [
        'ストーリーがしっかりしていて、エ〇だけじゃない魅力がある。キャラの心理描写も丁寧で読み応えあり',
        '絵が綺麗で表現力が高い。ストーリー展開も面白くて、普通のマンガとして楽しめる完成度',
        'シチュエーションが多彩で飽きない。キャラクターに魅力があるから、感情移入しながら楽しめる',
        '大人の夜を彩るのに最適な作品。ストーリーも絵もクオリティが高くて満足度が高い'
    ],
    'adult_novel': [
        '官能的なシーンもストーリーの一部として自然に溶け込んでいて、没入感がすごい。文章力が高い',
        '心理描写が巧みで、登場人物の感情の揺れ動きがリアル。読み進めるうちにどんどん引き込まれる',
        'エ〇ティックなだけでなく、人間関係や心の機微が丁寧に描かれている。大人だからこそ楽しめる深みがある',
        '夜にゆっくり読むのにぴったり。ストーリーがしっかりしているから、読後の満足感が高い'
    ],
    'adult_photo': [
        '写真のクオリティが高く、表情や雰囲気が魅力的。見ているだけで癒される美しさ',
        '構図や光の使い方が秀逸で、芸術性も感じられる。ただのグラビアじゃない、作品としての完成度',
        '自然体の魅力が引き出されていて、見ていて心地よい。ページをめくるたびに新しい発見がある',
        'ビジュアルの美しさはもちろん、雰囲気作りも素晴らしい。目の保養になる一冊'
    ],
    'adult_bl': [
        '心理描写が深く、二人の関係性に感情移入してしまう。エ〇ティックなシーンも含めて一つのストーリーとして完成度が高い',
        '大人だからこその葛藤や感情の揺れが丁寧に描かれている。読後の余韻が長く残る作品',
        'キャラクターの魅力が際立っていて、ストーリーにも引き込まれる。刺激的だけど品のある表現',
        '恋愛の機微が繊細に描かれていて、心が揺さぶられる。読み応えのある大人のBL作品'
    ],
    'adult_tl': [
        '甘く切ないストーリーに刺激的なシーンが絶妙に絡み合う。大人の女性の恋愛がリアルに描かれている',
        'キャラクターの心情が丁寧で、感情移入しながら楽しめる。エ〇ティックなだけじゃない深みがある',
        '官能的なシーンも含めてストーリーとして成立している。夜にゆっくり楽しみたい作品',
        '大人だからこその恋愛の駆け引きが面白い。ドキドキと切なさが交互に押し寄せる'
    ]
}

# 追加コメント（より具体的で深い）
ADDITIONAL_COMMENTS = [
    '立ち読みで数ページ読んだだけで続きが気になって購入してしまった',
    'セリフ回しが秀逸で、キャラクターの個性がしっかり立っている',
    '絵柄が好みで、コマ割りや構図も計算されている。読みやすさも◎',
    '展開が予測できないから、最後まで飽きずに読める。伏線回収も見事',
    'キャラの表情の描き分けが素晴らしく、感情が伝わってくる',
    'ストーリーのテンポが絶妙で、引き込まれるように読み進められる',
    '何度も読み返したくなる。読むたびに新しい発見がある作品',
    'このジャンルが好きなら絶対に読むべき。期待を裏切らない完成度'
]

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
                'item': item,
                'is_adult': False
            })
    
    # 成人向けカテゴリ
    for category_id, category_data in data.get('adult_categories', {}).items():
        for item in category_data.get('items', []):
            all_items.append({
                'type': 'adult',
                'category_id': category_id,
                'category_name': category_data['name'],
                'item': item,
                'is_adult': True
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

def censor_text(text, is_adult=False):
    """テキストを検閲"""
    # 成人向けの追加伏字
    if is_adult:
        adult_words = {
            'アダルト': 'ア〇ルト',
            'エロ': 'エ〇',
            '成人': '成〇',
            '官能': '官〇'
        }
        for word, replacement in adult_words.items():
            text = text.replace(word, replacement)
    
    return text

def download_image(image_url, should_blur=False):
    """画像をダウンロード（必要に応じてぼかし）"""
    try:
        print(f"🖼️  Downloading image from: {image_url}")
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()
        
        image = Image.open(BytesIO(response.content))
        print(f"✅ Image downloaded: {image.size}")
        
        # 成人向けの場合はぼかし適用
        if should_blur:
            image = image.filter(ImageFilter.GaussianBlur(radius=5))
            print(f"✅ Applied blur (radius=5)")
        
        output = BytesIO()
        image.save(output, format='JPEG', quality=85)
        output.seek(0)
        
        return output
        
    except Exception as e:
        print(f"❌ Error processing image: {e}")
        return None

def create_tweet_text(selected):
    """投稿テキストを生成（感想付き）"""
    import random
    
    item = selected['item']
    category_id = selected['category_id']
    category_name = selected['category_name']
    is_adult = selected['is_adult']
    
    # タイトルを検閲
    title = censor_text(item.get('title', 'タイトル不明'), is_adult=is_adult)
    
    # 立ち読みリンクを優先、なければアフィリエイトリンク
    url = item.get('sampleURL', item.get('affiliateURL', item.get('URL', '')))
    
    # タイトルを50文字に制限（感想文のスペースを確保）
    if len(title) > 50:
        title = title[:47] + '...'
    
    # カテゴリ名も検閲
    category_name = censor_text(category_name, is_adult=is_adult)
    
    # ジャンル別コメントを取得
    genre_comments = GENRE_COMMENTS.get(category_id, ['注目の一冊。ストーリーがしっかりしていて読み応えあり'])
    main_comment = random.choice(genre_comments)
    
    # 追加コメントをランダム選択（80%の確率で追加）
    additional = ''
    if random.random() > 0.2:
        additional = '\n\n' + random.choice(ADDITIONAL_COMMENTS)
    
    # 投稿テキストを組み立て
    tweet = f"{title}\n\n{main_comment}{additional}\n\n📖 {category_name}\n\n{url}"
    
    # Twitter文字数制限（280文字）チェック
    if len(tweet) > 280:
        # 追加コメントを削除
        tweet = f"{title}\n\n{main_comment}\n\n📖 {category_name}\n\n{url}"
    
    if len(tweet) > 280:
        # それでも長い場合はメインコメントを短縮
        main_comment_short = main_comment.split('。')[0] + '。'
        tweet = f"{title}\n\n{main_comment_short}\n\n📖 {category_name}\n\n{url}"
    
    if len(tweet) > 280:
        # さらに長い場合はタイトルを短縮
        title = title[:30] + '...'
        tweet = f"{title}\n\n{main_comment_short}\n\n📖 {category_name}\n\n{url}"
    
    return tweet

def create_fallback_tweet():
    """フォールバックツイート（indexに誘導）"""
    return """孤独な夜のガイド

恋愛マンガ、BL、TL、ラノベなど
今夜を優しく満たす作品が見つかります

https://self-pleasure-jp.github.io/lonely-night-guide/"""

def post_tweet_with_image(tweet_text, image_data, is_adult=False):
    """画像付きツイートを投稿（成人向けの場合はセンシティブ設定）"""
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
            
            # センシティブ設定（成人向けの場合のみ）
            if is_adult:
                print("🔞 Setting media as SENSITIVE (Adult content)")
                api.create_media_metadata(media_id, alt_text="アダルトコンテンツ")
            else:
                print("📚 Setting media as GENERAL (Safe content)")
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
        post_tweet_with_image(tweet_text, None, is_adult=False)
        return
    
    # 全アイテムリスト作成
    all_items = build_all_items_list(data)
    if not all_items:
        print("⚠️ No items found, using fallback tweet")
        tweet_text = create_fallback_tweet()
        post_tweet_with_image(tweet_text, None, is_adult=False)
        return
    
    # カウンター取得
    counter = get_current_counter()
    
    # アイテム選択
    selected = select_item_by_counter(all_items, counter)
    if not selected:
        print("⚠️ Could not select item, using fallback tweet")
        tweet_text = create_fallback_tweet()
        post_tweet_with_image(tweet_text, None, is_adult=False)
        return
    
    # ツイート作成
    tweet_text = create_tweet_text(selected)
    
    # 画像取得（成人向けの場合はぼかし）
    item = selected['item']
    image_url = item.get('imageURL', {}).get('large') or item.get('imageURL', {}).get('small')
    
    image_data = None
    if image_url:
        is_adult = selected['is_adult']
        image_data = download_image(image_url, should_blur=is_adult)
    else:
        print("⚠️ No image URL found")
    
    print("\n" + "="*50)
    print("📝 Tweet preview:")
    print("="*50)
    print(f"Category Type: {'🔞 ADULT' if selected['is_adult'] else '📚 GENERAL'}")
    print(tweet_text)
    if image_data:
        blur_status = "Blurred" if selected['is_adult'] else "Clear"
        sensitive_status = "SENSITIVE" if selected['is_adult'] else "SAFE"
        print(f"\n🖼️  Image: {blur_status} ({sensitive_status})")
    print("="*50 + "\n")
    
    # 投稿（is_adultフラグを渡す）
    success = post_tweet_with_image(tweet_text, image_data, is_adult=selected['is_adult'])
    
    if success:
        new_counter = counter + 1
        save_counter(new_counter)
        print(f"✅ Counter updated: {counter} → {new_counter}")
    else:
        print("⚠️ Tweet failed, counter not updated")

if __name__ == "__main__":
    main()
