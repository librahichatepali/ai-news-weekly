import feedparser
import smtplib
import os
import time
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.header import Header

# 【目标源】专注于榜单搬运能力最强的平台
FEEDS = [
    "http://www.sykong.com/feed",                          # 手游那点事 (最稳的小游戏榜单搬运)
    "https://www.gamelook.com.cn/category/mini-game/feed",  # GameLook (深度题材分析)
    "https://www.vrtuoluo.cn/category/mini-game/feed",     # 游戏陀螺 (周榜/月榜常客)
    "https://www.youxichaguan.com/feed"                    # 游戏茶馆
]

# 【白名单】增加“抖音”和“微信”的权重
CORE_KEYWORDS = ["小游戏", "微信", "抖音", "榜单", "排行榜", "Top", "买量", "数据", "题材", "爆款"]
# 【黑名单】暂时保留最基本的干扰项，以便测试是否误伤
BLACK_LIST = ["元宇宙", "盒马", "犹他大学", "芯片", "Vision Pro"]

def get_combined_report():
    # 🕒 调整到半年（180天），进行深度数据回溯测试
    cutoff = datetime.now() - timedelta(days=180)
    
    html = """
    <div style="max-width: 800px; margin: 0 auto; font-family: 'Microsoft YaHei', sans-serif; background: #f4f7f6; padding: 15px;">
        <div style="background: #007AFF; color: white; padding: 25px; text-align: center; border-radius: 12px 12px 0 0;">
            <h1 style="margin: 0; font-size: 20px;">🛡️ 小游戏·半年期深度打捞测试</h1>
            <p style="margin: 5px 0 0; opacity: 0.9; font-size: 13px;">专注于微信/抖音榜单搬运 | 回溯周期：180天</p>
        </div>
    """
    
    found_articles = []
    for url in FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:100]: # 每个源增加抓取条数上限
                pub_time = datetime(*entry.published_parsed[:6]) if hasattr(entry, 'published_parsed') else None
                
                # 时间过滤（半年内）
                if pub_time and pub_time < cutoff: continue

                title = entry.title
                summary = entry.get('summary', entry.get('description', ''))
                combined = (title + summary).lower()
                
                # 匹配逻辑
                is_hit = any(w.lower() in combined for w in CORE_KEYWORDS)
                is_blocked = any(w.lower() in combined for w in BLACK_LIST)
                
                if is_hit and not is_blocked:
                    if title not in [a['title'] for a in found_articles]:
                        found_articles.append({
                            'title': title,
                            'link': entry.link,
                            'summary': summary[:200] + "...",
                            'date': pub_time.strftime("%Y-%m-%d") if pub_time else "近期",
                            'source': f"{feed.feed.get('title', '行业源')}"
                        })
        except: continue

    html += '<div style="background: white; padding: 20px; border-radius: 0 0 12px 12px; border: 1px solid #e0e0e0; border-top: none;">'
    
    if not found_articles:
        html += """
        <div style="text-align:center; padding: 50px; color: #999;">
            <p>🔍 180 天内未发现匹配内容。</p>
            <p style="font-size: 12px;">这通常意味着 GitHub 海外 IP 抓取受限或屏蔽词（Blacklist）过于严格。</p>
        </div>
        """
    else:
        html += f"<p style='color: #666; font-size: 12px; margin-bottom: 15px;'>✅ 成功打捞到 {len(found_articles)} 条半年内相关资讯：</p>"
        for art in found_articles:
            # 特别标注“微信”或“抖音”字样
            platform_tag = ""
            if "微信" in art['title']: platform_tag = "<span style='background:#07C160; color:white; padding:2px 5px; border-radius:3px; font-size:10px; margin-right:5px;'>微信</span>"
            if "抖音" in art['title']: platform_tag = "<span style='background:#FF0050; color:white; padding:2px 5px; border-radius:3px; font-size:10px; margin-right:5px;'>抖音</span>"
            
            html += f"""
            <div style="border-bottom: 1px solid #f0f0f0; padding: 15px 0;">
                <h3 style="margin: 0 0 8px 0; font-size: 14px;">
                    {platform_tag}<a href="{art['link']}" style="color: #007AFF; text-decoration: none;">{art['title']}</a>
                </h3>
                <div style="font-size: 12px; color: #888;">⏱ {art['date']} | 📍 {art['source']}</div>
            </div>
            """
    
    html += "</div></div>" 
    return html

def send_mail(content):
    sender = os.environ.get('EMAIL_USER')
    password = str(os.environ.get('EMAIL_PASS')).strip()
    receiver = '249869251@qq.com'
    msg = MIMEText(content, 'html', 'utf-8')
    msg['From'] = f"DataMiner <{sender}>"
    msg['To'] = receiver
    msg['Subject'] = Header(f'📊 半年期深度情报打捞 - {time.strftime("%m-%d")}', 'utf-8')
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.starttls()
            server.login(sender, password)
            server.sendmail(sender, [receiver], msg.as_string())
        print("✅ 发送成功")
    except Exception as e:
        print(f"❌ 失败: {e}")

if __name__ == "__main__":
    report_html = get_combined_report()
    send_mail(report_html)
