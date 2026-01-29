import feedparser
import smtplib
import os
import time
from email.mime.text import MIMEText
from email.header import Header

# 【精选源】只保留高概率产出“小游戏”内容的垂直频道
FEEDS = [
    "https://www.gamelook.com.cn/category/mini-game/feed",  # GameLook小游戏专栏（最精准）
    "https://www.vrtuoluo.cn/category/news/feed",         # 游戏陀螺-行业新闻（虽然有杂讯，但榜单多）
    "https://www.youxichaguan.com/feed"                    # 游戏茶馆
]

# 【白名单】必须包含以下任意一个词，才会被收入邮件
WHITE_LIST = ["小游戏", "微信", "抖音", "快手", "榜单", "排行榜", "买量", "爆款", "题材", "分成"]

# 【黑名单】只要包含以下任意一个词，哪怕有“小游戏”也会被剔除（解决VR陀螺干扰）
BLACK_LIST = ["VR", "AR", "XR", "元宇宙", "Meta", "头显", "Metaverse", "Apple Vision", "神经腕带"]

def get_aggregated_news():
    full_content = """
    <div style="max-width: 800px; margin: 0 auto; font-family: 'Microsoft YaHei', sans-serif;">
        <div style="background: #07C160; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0;">
            <h1 style="margin: 0; font-size: 22px;">🎯 纯净小游戏行业周报</h1>
            <p style="margin: 5px 0 0; opacity: 0.8;">已自动过滤 VR/元宇宙等无关干扰</p>
        </div>
        <div style="background: white; padding: 20px; border: 1px solid #eee; border-top: none;">
    """
    
    found_articles = []
    
    for url in FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:30]: # 扩大扫描范围，提高打捞率
                title = entry.title
                summary = entry.get('summary', entry.get('description', ''))
                combined_text = (title + summary).lower()
                
                # 核心过滤逻辑：在白名单内 且 不在黑名单内
                is_useful = any(word.lower() in combined_text for word in WHITE_LIST)
                is_annoying = any(word.lower() in combined_text for word in BLACK_LIST)
                
                if is_useful and not is_annoying:
                    if title not in [a['title'] for a in found_articles]:
                        found_articles.append({
                            'title': title,
                            'link': entry.link,
                            'summary': summary[:400] + "..." if len(summary) > 400 else summary,
                            'source': feed.feed.get('title', '行业动态')
                        })
        except Exception as e:
            print(f"解析 {url} 出错: {e}")

    if not found_articles:
        full_content += "<p style='text-align:center; padding: 50px; color: #999;'>今日暂无匹配的纯净小游戏资讯。</p>"
    else:
        for art in found_articles:
            full_content += f"""
            <div style="margin-bottom: 25px; padding: 15px; border-left: 4px solid #07C160; background: #fcfcfc;">
                <h3 style="margin: 0 0 10px 0;"><a href="{art['link']}" style="color: #333; text-decoration: none;">{art['title']}</a></h3>
                <div style="font-size: 14px; color: #666; line-height: 1.7;">{art['summary']}</div>
                <div style="margin-top: 10px; font-size: 12px; color: #999;">来源：{art['source']}</div>
            </div>
            """

    full_content += "</div></div>"
    return full_content

def send_mail(content):
    sender = os.environ.get('EMAIL_USER')
    password = str(os.environ.get('EMAIL_PASS')).strip()
    receiver = '249869251@qq.com'
    
    msg = MIMEText(content, 'html', 'utf-8')
    msg['From'] = f"SmallGameBot <{sender}>"
    msg['To'] = receiver
    msg['Subject'] = Header(f'📊 小游戏垂直情报 ({time.strftime("%m-%d")})', 'utf-8')

    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.starttls()
            server.login(sender, password)
            server.sendmail(sender, [receiver], msg.as_string())
        print("✅ 精准情报发送成功！")
    except Exception as e:
        print(f"❌ 发送失败: {e}")

if __name__ == "__main__":
    news = get_aggregated_news()
    send_mail(news)
