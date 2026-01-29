import feedparser
import smtplib
import os
import time
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.header import Header

# 精选垂直源，重点加强 DataEye 榜单权重
FEEDS = [
    "https://www.dataeye.com/rss",                         # DataEye(榜单情报最强)
    "https://www.gamelook.com.cn/category/mini-game/feed",  # GameLook
    "https://www.vrtuoluo.cn/category/mini-game/feed",     # 游戏陀螺
    "http://www.sykong.com/feed"                           # 手游那点事
]

# 核心关键词：榜单类词汇会触发“置顶”样式
RANK_WORDS = ["榜单", "排行榜", "Top", "买量榜", "人气榜"]
MINI_GAME_WORDS = ["小游戏", "微信", "抖音", "快手", "IAA", "IAP"]

def get_aggregated_news():
    # 维持 15 天回溯，确保能抓到最近的一次周榜或月榜
    cutoff = datetime.now() - timedelta(days=15)
    
    # 邮件头部样式
    full_content = """
    <div style="max-width: 800px; margin: 0 auto; font-family: 'Microsoft YaHei', sans-serif; background: #f4f7f6; padding: 20px;">
        <div style="background: #07C160; color: white; padding: 25px; text-align: center; border-radius: 12px 12px 0 0; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <h1 style="margin: 0; font-size: 22px;">📊 小游戏 15 日榜单与题材专报</h1>
            <p style="margin: 8px 0 0; opacity: 0.9; font-size: 14px;">已聚合 DataEye 核心榜单与垂直媒体精华</p>
        </div>
        <div style="background: white; padding: 20px; border-radius: 0 0 12px 12px; border: 1px solid #e0e0e0; border-top: none;">
    """
    
    ranking_articles = [] # 存储榜单类
    general_articles = [] # 存储普通资讯类

    for url in FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                pub_time = None
                if hasattr(entry, 'published_parsed'):
                    pub_time = datetime(*entry.published_parsed[:6])
                if pub_time and pub_time < cutoff: continue

                title = entry.title
                summary = entry.get('summary', entry.get('description', '')).replace('<img', '<img style="max-width:100%; height:auto;" ')
                
                # 判定是否为小游戏相关
                is_about_game = any(w.lower() in title.lower() for w in MINI_GAME_WORDS)
                if not is_about_game: continue

                # 判定是否为榜单类
                is_rank = any(w.lower() in title.lower() for w in RANK_WORDS)
                
                article_data = {
                    'title': title,
                    'link': entry.link,
                    'summary': summary[:400] + "...",
                    'date': pub_time.strftime("%m-%d") if pub_time else "近期",
                    'source': feed.feed.get('title', '垂直媒体')
                }

                if is_rank:
                    if title not in [a['title'] for a in ranking_articles]:
                        ranking_articles.append(article_data)
                else:
                    if title not in [a['title'] for a in general_articles]:
                        general_articles.append(article_data)
        except Exception:
            continue

    # 1. 先渲染【核心榜单直击】板块
    if ranking_articles:
        full_content += '<div style="margin-bottom: 30px;"><h2 style="color: #07C160; border-bottom: 2px solid #07C160; padding-bottom: 5px;">🔥 核心榜单直击</h2>'
        for art in ranking_articles:
            full_content += f"""
            <div style="margin-top: 15px; padding: 15px; background: #f0fff4; border: 1px dashed #07C160; border-radius: 8px;">
                <h3 style="margin: 0 0 10px 0;"><a href="{art['link']}" style="color: #2c3e50; text-decoration: none;">【榜单】{art['title']}</a></h3>
                <div style="font-size: 14px; color: #444; line-height: 1.6;">{art['summary']}</div>
                <div style="margin-top: 10px; font-size: 12px; color: #888;">⏱ {art['date']} | 📍 {art['source']}</div>
            </div>
            """
        full_content += '</div>'

    # 2. 再渲染【行业题材精选】板块
    if general_articles:
        full_content += '<div style="margin-bottom: 20px;"><h2 style="color: #333; border-bottom: 2px solid #eee; padding-bottom: 5px;">📰 行业题材精选</h2>'
        for art in general_articles[:10]: # 普通新闻限10条，防止过长
            full_content += f"""
            <div style="margin-top: 15px; border-bottom: 1px solid #f0f0f0; padding-bottom: 15px;">
                <h4 style="margin: 0 0 8px 0; font-size: 16px;"><a href="{art['link']}" style="color: #007bff; text-decoration: none;">{art['title']}</a></h4>
                <div style="font-size: 13px; color: #666;">{art['summary']}</div>
                <div style="margin-top: 8px; font-size: 11px; color: #aaa;">{art['date']} | {art['source']}</div>
            </div>
            """
        full_content += '</div>'

    if not ranking_articles and not general_articles:
        full_content += "<p style='text-align:center; padding: 50px; color: #999;'>近 15 天暂未打捞到匹配的小游戏榜单或题材情报。</p>"

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
    msg['Subject'] = Header(f'📊 小游戏榜单优先专报 - {time.strftime("%m-%d")}', 'utf-8')
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.starttls()
            server.login(sender, password)
            server.sendmail(sender, [receiver], msg.as_string())
        print("✅ 榜单专报发送成功！")
    except Exception as e: print(f"❌ 发送失败: {e}")

if __name__ == "__main__":
    news = get_aggregated_news()
    send_mail(news)
