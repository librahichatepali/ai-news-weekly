import feedparser
import smtplib
import os
import time
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.header import Header

# 【核心搬运源】这些是目前最稳、最专业的搬运和解读平台
FEEDS = [
    "http://www.sykong.com/feed",                          # 手游那点事 (DataEye榜单核心搬运者)
    "https://www.gamelook.com.cn/category/mini-game/feed",  # GameLook (小游戏题材深度分析)
    "https://www.vrtuoluo.cn/category/mini-game/feed",     # 游戏陀螺 (微信/抖音小游戏周榜常驻)
    "https://www.youxichaguan.com/feed"                    # 游戏茶馆 (小游戏买量动态)
]

# 【白名单】强制包含以下词汇的文章才会被打捞
CORE_KEYWORDS = ["小游戏", "微信", "抖音", "榜单", "排行榜", "Top", "买量"]
# 【黑名单】强制排除干扰项，彻底告别“盒马”和“犹他大学”
BLACK_LIST = ["元宇宙", "盒马", "犹他大学", "VR", "AR", "Vision Pro", "芯片", "建厂"]

def get_aggregated_news():
    # 扩大搜索范围到 15 天，确保每周的榜单周报都能被覆盖
    cutoff = datetime.now() - timedelta(days=15)
    
    full_content = """
    <div style="max-width: 800px; margin: 0 auto; font-family: 'Microsoft YaHei', sans-serif;">
        <div style="background: #07C160; color: white; padding: 25px; text-align: center; border-radius: 12px 12px 0 0;">
            <h1 style="margin: 0; font-size: 22px;">📊 小游戏榜单 & 题材全网打捞</h1>
            <p style="margin: 8px 0 0; opacity: 0.9;">已整合手游那点事、GameLook等 4 大搬运平台数据</p>
        </div>
        <div style="background: white; padding: 20px; border: 1px solid #e0e0e0; border-top: none;">
    """
    
    found_articles = []

    for url in FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:100]: # 每个源检索 50 条最新内容
                pub_time = None
                if hasattr(entry, 'published_parsed'):
                    pub_time = datetime(*entry.published_parsed[:6])
                
                # 时间过滤
                if pub_time and pub_time < cutoff: continue

                title = entry.title
                summary = entry.get('summary', entry.get('description', ''))
                combined_text = (title + summary).lower()
                
                # 检查白名单命中情况
                is_hit = any(word.lower() in combined_text for word in CORE_KEYWORDS)
                # 检查黑名单屏蔽情况
                is_blocked = any(word.lower() in combined_text for word in BLACK_LIST)
                
                if is_hit and not is_blocked:
                    if title not in [a['title'] for a in found_articles]:
                        found_articles.append({
                            'title': title,
                            'link': entry.link,
                            'summary': summary[:400] + "...",
                            'date': pub_time.strftime("%m-%d") if pub_time else "近期",
                            'source': f"{feed.feed.get('title', '垂直渠道')}"
                        })
        except: continue

    if not found_articles:
        full_content += "<p style='text-align:center; padding: 50px; color: #999;'>🔍 近 15 天搬运平台暂未更新相关榜单文章。</p>"
    else:
        for art in found_articles:
            # 如果是榜单类内容，增加视觉高亮
            box_style = "border-left: 5px solid #ff4500; background: #fff5f0;" if "榜" in art['title'] else "border-left: 5px solid #07C160; background: #fcfcfc;"
            full_content += f"""
            <div style="margin-bottom: 25px; padding: 15px; {box_style} border-radius: 4px;">
                <h3 style="margin: 0 0 10px 0;"><a href="{art['link']}" style="color: #2c3e50; text-decoration: none;">{art['title']}</a></h3>
                <div style="font-size: 14px; color: #444; line-height: 1.6;">{art['summary']}</div>
                <div style="margin-top: 10px; font-size: 12px; color: #888;">⏱ {art['date']} | 📍 {art['source']}</div>
            </div>
            """

    full_content += "</div></div>"
    return full_content

# 后续 send_mail 函数保持不变...
def send_mail(content):
    sender = os.environ.get('EMAIL_USER')
    password = str(os.environ.get('EMAIL_PASS')).strip()
    receiver = '249869251@qq.com'
    msg = MIMEText(content, 'html', 'utf-8')
    msg['From'] = f"SmallGameBot <{sender}>"
    msg['To'] = receiver
    msg['Subject'] = Header(f'📊 小游戏搬运榜单专报 - {time.strftime("%m-%d")}', 'utf-8')
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
