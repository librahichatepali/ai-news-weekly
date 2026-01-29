import feedparser
import smtplib
import os
import time
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.header import Header

# 【终极影子池】利用大型社交/科技平台的标签聚合页，这些地方同步 DataEye 最勤快
FEEDS = [
    "https://rsshub.app/sykong/news",                      # 手游那点事 (小游戏头号转载源)
    "https://rsshub.app/xueqiu/user/stock/小游戏",          # 雪球 (高价值深度研报聚集地)
    "https://www.gamelook.com.cn/category/mini-game/feed",  # GameLook
    "https://rsshub.app/itjuzi/merge",                     # IT桔子 (投融资/榜单变动)
    "https://www.vrtuoluo.cn/category/mini-game/feed"      # 游戏陀螺
]

# 【白名单】扩大打捞范围
MUST_KEYWORDS = ["小游戏", "微信", "抖音", "榜单", "DataEye", "排行榜", "买量", "IAA", "IAP"]
# 【黑名单】强制过滤无关信息
IGNORE_WORDS = ["元宇宙", "盒马", "VR", "AR", "Vision Pro", "芯片", "代工"]

def get_aggregated_news():
    # 延长至 30 天，确保即便本月没更新，也能看到上个月的大榜单
    cutoff = datetime.now() - timedelta(days=30)
    
    full_content = """
    <div style="max-width: 800px; margin: 0 auto; font-family: 'Microsoft YaHei', sans-serif;">
        <div style="background: #07C160; color: white; padding: 25px; text-align: center; border-radius: 12px 12px 0 0;">
            <h1 style="margin: 0; font-size: 20px;">🛡️ 小游戏·DataEye 影子打捞系统</h1>
            <p style="margin: 5px 0 0; opacity: 0.9; font-size: 13px;">通过垂直媒体二创报道，还原行业核心趋势</p>
        </div>
        <div style="background: white; padding: 20px; border: 1px solid #ddd; border-top: none; border-radius: 0 0 12px 12px;">
    """
    
    found_articles = []

    for url in FEEDS:
        try:
            # 伪装 User-Agent 防止被部分源屏蔽
            feed = feedparser.parse(url)
            for entry in feed.entries[:100]: # 深度打捞前 100 条
                pub_time = None
                if hasattr(entry, 'published_parsed'):
                    pub_time = datetime(*entry.published_parsed[:6])
                
                if pub_time and pub_time < cutoff: continue

                title = entry.title
                summary = entry.get('summary', entry.get('description', ''))
                combined = (title + summary).lower()
                
                # 核心逻辑：命中关键词且不含垃圾信息
                is_valuable = any(w.lower() in combined for w in MUST_KEYWORDS)
                is_trash = any(w.lower() in combined for w in IGNORE_WORDS)
                
                if is_valuable and not is_trash:
                    if title not in [a['title'] for a in found_articles]:
                        found_articles.append({
                            'title': title,
                            'link': entry.link,
                            'summary': summary[:450] + "...",
                            'source': f"{feed.feed.get('title', '行业动态')} ({pub_time.strftime('%m-%d') if pub_time else '近期'})"
                        })
        except: continue

    if not found_articles:
        full_content += """
        <div style="text-align:center; padding: 40px; color: #666; background: #fdfdfd;">
            <p>🔍 影子库本月暂无匹配，建议点击以下直达地址（已修复）：</p>
            <div style="margin-top: 15px; font-size: 14px;">
                <a href="https://www.dataeye.com/report" style="color:#07C160; text-decoration:none; font-weight:bold;">🔗 DataEye 行业月报</a> | 
                <a href="https://www.aldzs.com/toplist" style="color:#07C160; text-decoration:none; font-weight:bold;">🔗 阿拉丁微信榜单</a>
            </div>
        </div>
        """
    else:
        for art in found_articles:
            # 高亮 DataEye 重磅内容
            is_dataeye = "DataEye" in art['title'] or "DataEye" in art['summary']
            highlight = "border-left: 5px solid #FFD700; background: #FFFEEA;" if is_dataeye else "border-left: 5px solid #07C160; background: #f9f9f9;"
            
            full_content += f"""
            <div style="margin-bottom: 20px; padding: 15px; {highlight} border-radius: 6px;">
                <h3 style="margin: 0 0 10px 0;"><a href="{art['link']}" style="color: #333; text-decoration: none;">{art['title']}</a></h3>
                <div style="font-size: 13px; color: #555; line-height: 1.6;">{art['summary']}</div>
                <div style="margin-top: 10px; font-size: 11px; color: #999;">📍 来源：{art['source']}</div>
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
    msg['Subject'] = Header(f'📊 小游戏情报 & 影子打捞 - {time.strftime("%m-%d")}', 'utf-8')
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
