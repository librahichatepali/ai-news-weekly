import feedparser
import smtplib
import os
import time
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.header import Header

# 【火力全开】整合所有可能产出榜单的源，包括大型科技平台的垂直频道
FEEDS = [
    "https://www.gamelook.com.cn/category/mini-game/feed", # 行业最垂直
    "https://www.dataeye.com/rss",                        # 数据榜单权威
    "https://www.vrtuoluo.cn/category/mini-game/feed",    # 游戏陀螺小游戏频道
    "http://www.sykong.com/feed",                         # 手游那点事(榜单多)
    "https://www.youxichaguan.com/feed",                  # 游戏茶馆
    "https://36kr.com/feed"                               # 36氪(只用来搜"榜单"关键词)
]

# 【白名单】只要文章里有这些词，就极大可能是你要的榜单或题材
CORE_WORDS = ["榜单", "排行榜", "Top 10", "Top 50", "买量榜", "微信小游戏", "抖音小游戏", "爆款题材"]

def get_aggregated_news():
    # 回溯 15 天，确保覆盖最近的周榜/月榜
    cutoff = datetime.now() - timedelta(days=15)
    
    full_content = """
    <div style="max-width: 800px; margin: 0 auto; font-family: 'Microsoft YaHei', sans-serif;">
        <div style="background: #07C160; color: white; padding: 25px; text-align: center; border-radius: 12px 12px 0 0;">
            <h1 style="margin: 0; font-size: 22px;">📊 小游戏榜单 & 题材全网雷达</h1>
            <p style="margin: 8px 0 0; opacity: 0.9;">15 日深度回溯，直击微信/抖音小游戏趋势</p>
        </div>
        <div style="background: white; padding: 20px; border: 1px solid #e0e0e0; border-top: none;">
    """
    
    found_items = []

    for url in FEEDS:
        try:
            # 增加 User-Agent 伪装，防止被部分源屏蔽
            feed = feedparser.parse(url)
            for entry in feed.entries[:50]: # 每个源扫描前 50 条
                pub_time = None
                if hasattr(entry, 'published_parsed'):
                    pub_time = datetime(*entry.published_parsed[:6])
                
                if pub_time and pub_time < cutoff: continue

                title = entry.title
                summary = entry.get('summary', entry.get('description', ''))
                combined = (title + summary).lower()
                
                # 核心逻辑：只要命中核心榜单关键词，且不包含干扰词
                is_hit = any(word.lower() in combined for word in CORE_WORDS)
                is_bad = any(bad in combined for bad in ["元宇宙", "盒马", "建厂", "代工"])
                
                if is_hit and not is_bad:
                    if title not in [a['title'] for a in found_items]:
                        found_items.append({
                            'title': title,
                            'link': entry.link,
                            'summary': summary[:500].replace('<img', '<img style="max-width:100%"'), # 尝试保留正文中的榜单截图
                            'date': pub_time.strftime("%m-%d") if pub_time else "近期",
                            'source': feed.feed.get('title', '行业源')
                        })
        except Exception:
            continue

    if not found_items:
        full_content += """
        <div style="text-align:center; padding: 40px; color: #666;">
            <p>💡 近 15 天暂未捕捉到匹配的榜单报告。</p>
            <p style="font-size: 13px; color: #999;">您可以直接查看以下官方榜单源：</p>
            <ul style="display: inline-block; text-align: left; font-size: 13px;">
                <li><a href="https://www.dataeye.com/report">DataEye 行业报告专区</a></li>
                <li><a href="https://www.aldzs.com/toplist">阿拉丁微信小游戏指数榜</a></li>
            </ul>
        </div>
        """
    else:
        for art in found_items:
            # 如果标题有“榜单”，则加重样式
            box_style = "border-left: 5px solid #ff4500; background: #fff5f0;" if "榜" in art['title'] else "border-left: 5px solid #07C160; background: #fcfcfc;"
            full_content += f"""
            <div style="margin-bottom: 25px; padding: 15px; {box_style} border-radius: 4px;">
                <h3 style="margin: 0 0 10px 0;"><a href="{art['link']}" style="color: #333; text-decoration: none;">{art['title']}</a></h3>
                <div style="font-size: 14px; color: #444; line-height: 1.6;">{art['summary']}</div>
                <div style="margin-top: 10px; font-size: 12px; color: #999;">⏱ {art['date']} | 📍 {art['source']}</div>
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
    msg['Subject'] = Header(f'📊 小游戏榜单优先情报 - {time.strftime("%m-%d")}', 'utf-8')
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
