import feedparser
import smtplib
import os
import time
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.header import Header

# 【混合信源库】涵盖垂直媒体、行业榜单、及大型平台的标签聚合页
FEEDS = [
    "https://www.gamelook.com.cn/category/mini-game/feed", # GameLook小游戏(最稳)
    "https://www.vrtuoluo.cn/category/news/feed",         # 游戏陀螺
    "https://www.youxichaguan.com/feed",                  # 游戏茶馆
    "https://www.dataeye.com/rss",                        # DataEye(数据榜单)
    "http://www.sykong.com/feed",                         # 手游那点事
    "https://36kr.com/feed",                               # 36氪全量(作为兜底)
    "https://www.ithome.com/rss/game.xml"                 # IT之家游戏频道
]

# 【白名单】扩大行业黑话库，提高打捞命中率
WHITE_LIST = [
    "小游戏", "微信", "抖音", "快手", "榜单", "排行榜", "上升最快",
    "爆款题材", "研报", "出海", "IAA", "IAP", "转化率", "小游戏赛道"
]

# 【黑名单】精准排除，防止“盒马”等社会新闻再次出现
BLACK_LIST = ["元宇宙", "盒马", "经济增速", "VR头显", "Metaverse", "Vision Pro"]

def get_aggregated_news():
    # 延长回溯周期至 15 天，确保有内容可看
    search_cutoff = datetime.now() - timedelta(days=15)
    
    full_content = """
    <div style="max-width: 800px; margin: 0 auto; font-family: 'Microsoft YaHei', sans-serif;">
        <div style="background: #07C160; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0;">
            <h1 style="margin: 0; font-size: 20px;">🎮 小游戏题材全网打捞 (15日精选)</h1>
            <p style="margin: 5px 0 0; opacity: 0.8;">已整合 7 大核心信源，自动过滤非相关行业杂讯</p>
        </div>
        <div style="background: white; padding: 20px; border: 1px solid #eee; border-top: none;">
    """
    
    found_articles = []
    
    for url in FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:60]: # 加大扫描深度，从海量信息中捞针
                published_time = None
                if hasattr(entry, 'published_parsed'):
                    published_time = datetime(*entry.published_parsed[:6])
                
                if published_time and published_time < search_cutoff:
                    continue

                title = entry.title
                summary = entry.get('summary', entry.get('description', ''))
                combined_text = (title + summary).lower()
                
                # 过滤逻辑：只要包含白名单词且不含黑名单词，就尝试收入
                contains_useful = any(word.lower() in combined_text for word in WHITE_LIST)
                contains_black = any(word.lower() in combined_text for word in BLACK_LIST)
                
                if contains_useful and not contains_black:
                    if title not in [a['title'] for a in found_articles]:
                        date_str = published_time.strftime("%m-%d") if published_time else "精选"
                        found_articles.append({
                            'title': title,
                            'link': entry.link,
                            'summary': summary[:300] + "...",
                            'source': f"{feed.feed.get('title', '行业动态')} ({date_str})"
                        })
        except Exception as e:
            print(f"解析 {url} 出错: {e}")

    # 按时间降序排列，让最新的排在前面
    if not found_articles:
        full_content += "<p style='text-align:center; padding: 50px; color: #999;'>近 15 天内暂无符合精准过滤条件的小游戏资讯。</p>"
    else:
        for art in found_articles[:20]: # 每次推送最多展示 20 条最相关的，防止过长
            full_content += f"""
            <div style="margin-bottom: 20px; padding: 12px; border-bottom: 1px solid #f0f0f0;">
                <h3 style="margin: 0 0 8px 0; font-size: 16px;"><a href="{art['link']}" style="color: #007bff; text-decoration: none;">{art['title']}</a></h3>
                <div style="font-size: 13px; color: #666; line-height: 1.6;">{art['summary']}</div>
                <div style="margin-top: 8px; font-size: 11px; color: #999;">📅 {art['source']}</div>
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
    msg['Subject'] = Header(f'📊 小游戏行业专报 (15日回溯) - {time.strftime("%m-%d")}', 'utf-8')

    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.starttls()
            server.login(sender, password)
            server.sendmail(sender, [receiver], msg.as_string())
        print("✅ 专报发送成功！")
    except Exception as e:
        print(f"❌ 发送失败: {e}")

if __name__ == "__main__":
    news = get_aggregated_news()
    send_mail(news)
