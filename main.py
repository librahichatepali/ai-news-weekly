import feedparser
import smtplib
import os
import time
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.header import Header

# 【多源打捞】既然 DataEye 官网难抓，我们抓取它的“深度合作伙伴”
FEEDS = [
    "http://www.sykong.com/feed",                          # 手游那点事（DataEye内容核心同步源）
    "https://www.gamelook.com.cn/category/mini-game/feed",  # GameLook（小游戏题材权威）
    "https://www.vrtuoluo.cn/category/mini-game/feed",     # 游戏陀螺（深度行业报告二创）
    "https://www.youxichaguan.com/feed"                    # 游戏茶馆
]

# 【白名单】加入 "DataEye" 作为核心关键词，确保哪怕是转载也能被捞到
WHITE_LIST = ["小游戏", "微信", "抖音", "DataEye", "榜单", "排行榜", "买量", "爆款", "题材"]
BLACK_LIST = ["元宇宙", "盒马", "VR", "AR", "Vision Pro"]

def get_aggregated_news():
    # 延长至 20 天，确保不漏掉 DataEye 产出的重磅周报或月报
    cutoff = datetime.now() - timedelta(days=20)
    
    full_content = """
    <div style="max-width: 800px; margin: 0 auto; font-family: 'Microsoft YaHei', sans-serif;">
        <div style="background: #07C160; color: white; padding: 25px; text-align: center; border-radius: 12px 12px 0 0;">
            <h1 style="margin: 0; font-size: 20px;">🛡️ 小游戏全网雷达 (含 DataEye 同步情报)</h1>
            <p style="margin: 8px 0 0; opacity: 0.9; font-size: 14px;">已整合 手游那点事、GameLook 等核心数据源</p>
        </div>
        <div style="background: white; padding: 20px; border: 1px solid #e0e0e0; border-top: none;">
    """
    
    found_items = []

    for url in FEEDS:
        try:
            # 增加对源的解析深度
            feed = feedparser.parse(url)
            for entry in feed.entries[:60]:
                pub_time = None
                if hasattr(entry, 'published_parsed'):
                    pub_time = datetime(*entry.published_parsed[:6])
                
                if pub_time and pub_time < cutoff: continue

                title = entry.title
                summary = entry.get('summary', entry.get('description', ''))
                combined = (title + summary).lower()
                
                # 逻辑：只要标题或正文提到 DataEye 或 核心词
                is_hit = any(word.lower() in combined for word in WHITE_LIST)
                is_bad = any(word.lower() in combined for word in BLACK_LIST)
                
                if is_hit and not is_bad:
                    if title not in [a['title'] for a in found_items]:
                        found_items.append({
                            'title': title,
                            'link': entry.link,
                            'summary': summary[:450],
                            'date': pub_time.strftime("%m-%d") if pub_time else "近期",
                            'source': f"{feed.feed.get('title', '垂直渠道')}"
                        })
        except Exception: continue

    if not found_items:
        full_content += "<p style='text-align:center; padding: 50px; color: #999;'>🔍 近 20 天内暂无匹配的小游戏或 DataEye 相关情报。</p>"
    else:
        for art in found_items:
            # 高亮显示包含 DataEye 的资讯
            highlight = "border-left: 5px solid #FFD700; background: #FFFDF0;" if "DataEye" in art['title'] or "DataEye" in art['summary'] else "border-left: 5px solid #07C160; background: #fcfcfc;"
            full_content += f"""
            <div style="margin-bottom: 25px; padding: 15px; {highlight} border-radius: 4px;">
                <h3 style="margin: 0 0 10px 0;"><a href="{art['link']}" style="color: #333; text-decoration: none;">{art['title']}</a></h3>
                <div style="font-size: 14px; color: #444; line-height: 1.6;">{art['summary']}</div>
                <div style="margin-top: 10px; font-size: 11px; color: #999;">📅 {art['date']} | 📍 {art['source']}</div>
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
    msg['Subject'] = Header(f'📊 小游戏情报 & DataEye 趋势 - {time.strftime("%m-%d")}', 'utf-8')
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.starttls()
            server.login(sender, password)
            server.sendmail(sender, [receiver], msg.as_string())
        print("✅ 专报发送成功！")
    except Exception as e: print(f"❌ 发送失败: {e}")

if __name__ == "__main__":
    news = get_aggregated_news()
    send_mail(news)
