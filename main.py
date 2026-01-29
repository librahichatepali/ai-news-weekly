import feedparser
import smtplib
import os
import time
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.header import Header

# 【最稳影子源】这些平台的 RSS 极少失效，且大量转载 DataEye 情报
FEEDS = [
    "https://rsshub.app/sykong/news",                      # 手游那点事全量(包含大量DataEye数据)
    "https://www.gamelook.com.cn/category/mini-game/feed",  # GameLook 精选
    "https://www.vrtuoluo.cn/category/mini-game/feed",     # 游戏陀螺小游戏
    "https://rsshub.app/xueqiu/user/stock/游戏",             # 雪球行业动态(备用打捞)
]

# 【白名单】加入对 "DataEye" 的强制打捞，只要合作伙伴提到它，我们就抓
MUST_KEYWORDS = ["小游戏", "微信", "抖音", "榜单", "DataEye", "排行榜", "买量"]
# 【黑名单】强制排除干扰项，解决“盒马”等杂讯
IGNORE_WORDS = ["元宇宙", "盒马", "VR", "代工", "芯片", "Vision Pro"]

def get_aggregated_news():
    # 增加回溯至 25 天，确保跨月的大榜单能被捞到
    cutoff = datetime.now() - timedelta(days=25)
    
    full_content = """
    <div style="max-width: 800px; margin: 0 auto; font-family: 'Microsoft YaHei', sans-serif; background: #f9f9f9; padding: 15px;">
        <div style="background: #07C160; color: white; padding: 25px; text-align: center; border-radius: 12px 12px 0 0;">
            <h1 style="margin: 0; font-size: 20px;">🛡️ 小游戏·DataEye 深度情报打捞</h1>
            <p style="margin: 5px 0 0; opacity: 0.8; font-size: 13px;">回溯合作伙伴情报，直击行业核心榜单</p>
        </div>
        <div style="background: white; padding: 20px; border: 1px solid #ddd; border-top: none; border-radius: 0 0 12px 12px;">
    """
    
    found_articles = []

    for url in FEEDS:
        try:
            feed = feedparser.parse(url)
            # 提高检索深度到 80 条
            for entry in feed.entries[:80]:
                pub_time = None
                if hasattr(entry, 'published_parsed'):
                    pub_time = datetime(*entry.published_parsed[:6])
                
                if pub_time and pub_time < cutoff: continue

                title = entry.title
                summary = entry.get('summary', entry.get('description', ''))
                combined_text = (title + summary).lower()
                
                # 检查是否包含核心硬词，且没有垃圾干扰
                contains_valuable = any(w.lower() in combined_text for w in MUST_KEYWORDS)
                is_irrelevant = any(w.lower() in combined_text for w in IGNORE_WORDS)
                
                if contains_valuable and not is_irrelevant:
                    if title not in [a['title'] for a in found_articles]:
                        found_articles.append({
                            'title': title,
                            'link': entry.link,
                            'summary': summary[:450] + "...",
                            'source': f"{feed.feed.get('title', '垂直渠道')} ({pub_time.strftime('%m-%d') if pub_time else '近期'})"
                        })
        except: continue

    if not found_articles:
        full_content += """
        <div style="text-align:center; padding: 50px; color: #888;">
            <p>🔍 影子库暂无匹配，建议查看以下直达链接（已修复）：</p>
            <div style="margin-top: 15px;">
                <a href="https://www.dataeye.com/report" style="color:#07C160;">🔗 DataEye 行业月报</a> | 
                <a href="https://www.aldzs.com/toplist" style="color:#07C160;">🔗 阿拉丁微信指数</a>
            </div>
        </div>
        """
    else:
        for art in found_articles:
            # 高亮包含 DataEye 的重磅情报
            is_dataeye = "DataEye" in art['title'] or "DataEye" in art['summary']
            style = "border-left: 5px solid #FFD700; background: #FFFEEA;" if is_dataeye else "border-left: 5px solid #07C160; background: #F8FCF9;"
            
            full_content += f"""
            <div style="margin-bottom: 20px; padding: 15px; {style} border-radius: 6px;">
                <h3 style="margin: 0 0 8px 0;"><a href="{art['link']}" style="color: #333; text-decoration: none;">{'[重磅] ' if is_dataeye else ''}{art['title']}</a></h3>
                <div style="font-size: 13px; color: #555; line-height: 1.6;">{art['summary']}</div>
                <div style="margin-top: 10px; font-size: 11px; color: #999;">📍 来自：{art['source']}</div>
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
    msg['Subject'] = Header(f'📊 小游戏情报打捞 - {time.strftime("%m-%d")}', 'utf-8')
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.starttls()
            server.login(sender, password)
            server.sendmail(sender, [receiver], msg.as_string())
        print("✅ 发送成功！")
    except Exception as e: print(f"❌ 发送失败: {e}")

if __name__ == "__main__":
    news_html = get_aggregated_news()
    send_mail(news_html)
