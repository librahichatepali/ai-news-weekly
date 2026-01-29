import feedparser
import smtplib
import os
import time
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.header import Header

# 【精选源】专注于微信/抖音小游戏题材拆解的垂直渠道 (通过代理中转)
FEEDS = [
    "https://rsshub.app/sykong/category/25",                # 手游那点事-小游戏专栏 (最稳榜单)
    "https://rsshub.app/gamelook/category/mini-game",        # GameLook-小游戏专题
    "https://rsshub.app/mp/msgalbum/MzI3MDUyODA3MA==/1587829280459341825" # 微信能量站(官方汇总)
]

# 【白名单】聚焦：榜单、题材、爆款、拆解、买量
CORE_KEYWORDS = ["小游戏", "微信", "抖音", "榜单", "排行", "题材", "买量", "消耗", "爆款", "内测"]
# 【黑名单】过滤干扰
BLACK_LIST = ["元宇宙", "盒马", "犹他大学", "芯片", "主机", "PC", "PS5"]

def get_report_html():
    cutoff = datetime.now() - timedelta(days=180) # 维持半年回溯进行压力测试
    
    # 1. 顶部：官方目录导航 (采用微信内部目录链接，降低404风险)
    html = """
    <div style="max-width: 700px; margin: 0 auto; font-family: 'Microsoft YaHei', sans-serif;">
        <div style="background: #07C160; color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0;">
            <h2 style="margin: 0;">🎮 小游戏题材 & 榜单监测</h2>
            <p style="margin: 5px 0 0; font-size: 12px; opacity: 0.8;">官方能量站 + 垂直自媒体打捞</p>
        </div>
        
        <div style="background: white; padding: 15px; border: 1px solid #eee; border-top: none;">
            <p style="font-size: 13px; color: #333; font-weight: bold; border-left: 3px solid #07C160; padding-left: 8px; margin-bottom: 12px;">📊 官方往期榜单目录 (必选):</p>
            <a href="https://mp.weixin.qq.com/mp/appmsgalbum?__biz=MzI3MDUyODA3MA==&action=getalbum&album_id=1587829280459341825#wechat_redirect" 
               style="display: block; background: #f9f9f9; padding: 12px; border-radius: 6px; text-decoration: none; color: #07C160; font-weight: bold; border: 1px solid #e1f2e9;">
               🔗 微信官方能量站 · 历次榜单汇总
            </a>
        </div>
    """

    # 2. 中间：动态打捞内容
    found_articles = []
    for url in FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:40]:
                pub_time = datetime(*entry.published_parsed[:6]) if hasattr(entry, 'published_parsed') else None
                if pub_time and pub_time < cutoff: continue
                
                title = entry.title
                summary = entry.get('summary', entry.get('description', ''))
                combined = (title + summary).lower()
                
                if any(w.lower() in combined for w in CORE_KEYWORDS) and not any(w.lower() in combined for w in BLACK_LIST):
                    if title not in [a['title'] for a in found_articles]:
                        found_articles.append({
                            'title': title,
                            'link': entry.link,
                            'date': pub_time.strftime("%Y-%m-%d") if pub_time else "近期"
                        })
        except: continue

    html += '<div style="background: white; padding: 15px; border: 1px solid #eee; border-top: none; border-radius: 0 0 10px 10px;">'
    html += '<p style="font-size: 13px; color: #333; font-weight: bold; border-left: 3px solid #ff9800; padding-left: 8px; margin-bottom: 12px;">🗞️ 近半年题材拆解 & 资讯:</p>'
    
    if not found_articles:
        html += "<p style='text-align:center; padding: 30px; color: #999; font-size: 12px;'>暂未通过代理打捞到垂直源更新，建议点上方【官方目录】。</p>"
    else:
        for art in found_articles:
            html += f"""
            <div style="margin-bottom: 12px; padding-bottom: 10px; border-bottom: 1px dashed #f0f0f0;">
                <a href="{art['link']}" style="color: #333; text-decoration: none; font-size: 14px;">• {art['title']}</a>
                <span style="color: #bbb; font-size: 11px; margin-left: 8px;">({art['date']})</span>
            </div>
            """
    
    html += "</div></div>"
    return html

def send_mail(content):
    sender = os.environ.get('EMAIL_USER')
    password = str(os.environ.get('EMAIL_PASS')).strip()
    receiver = '249869251@qq.com'
    msg = MIMEText(content, 'html', 'utf-8')
    msg['From'] = f"MiniGameRadar <{sender}>"
    msg['To'] = receiver
    msg['Subject'] = Header(f'🚀 小游戏题材打捞: {time.strftime("%m-%d")}', 'utf-8')
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.starttls()
            server.login(sender, password)
            server.sendmail(sender, [receiver], msg.as_string())
        print("✅ 发送成功")
    except Exception as e: print(f"❌ 失败: {e}")

if __name__ == "__main__":
    content = get_report_html()
    send_mail(content)
