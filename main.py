import feedparser
import smtplib
import os
import time
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.header import Header

# 【信源池】选取最稳的搬运平台源
FEEDS = [
    "http://www.sykong.com/feed",                          # 手游那点事
    "https://www.gamelook.com.cn/category/mini-game/feed",  # GameLook
    "https://www.vrtuoluo.cn/category/mini-game/feed",     # 游戏陀螺
    "https://www.youxichaguan.com/feed"                    # 游戏茶馆
]

CORE_KEYWORDS = ["小游戏", "微信", "抖音", "榜单", "排行榜", "Top", "买量", "DataEye"]
BLACK_LIST = ["元宇宙", "盒马", "犹他大学", "VR", "芯片", "Vision Pro"]

def get_combined_report():
    cutoff = datetime.now() - timedelta(days=20)
    
    # 1. 静态导航部分 (保底方案)
    html = """
    <div style="max-width: 800px; margin: 0 auto; font-family: 'Microsoft YaHei', sans-serif; background: #f4f7f6; padding: 15px;">
        <div style="background: #07C160; color: white; padding: 25px; text-align: center; border-radius: 12px 12px 0 0;">
            <h1 style="margin: 0; font-size: 20px;">🛡️ 小游戏·DataEye 数据专报</h1>
            <p style="margin: 5px 0 0; opacity: 0.9; font-size: 13px;">实时导航 + 全网搬运打捞系统</p>
        </div>
        
        <div style="background: white; padding: 20px; margin-bottom: 15px; border: 1px solid #e0e0e0; border-top: none; border-radius: 0 0 12px 12px;">
            <h2 style="font-size: 15px; color: #333; border-left: 4px solid #07C160; padding-left: 10px; margin-bottom: 15px;">🚀 实时榜单入口 (PC/移动通用)</h2>
            <div style="display: flex; gap: 10px; text-align: center;">
                <a href="https://www.dataeye.com/" style="flex: 1; text-decoration: none; background: #f9f9f9; padding: 12px; border-radius: 8px; border: 1px solid #eee;">
                    <div style="font-weight: bold; font-size: 14px; color: #07C160;">DataEye</div>
                    <div style="font-size: 10px; color: #999;">官网首页</div>
                </a>
                <a href="https://www.aldzs.com/" style="flex: 1; text-decoration: none; background: #f9f9f9; padding: 12px; border-radius: 8px; border: 1px solid #eee;">
                    <div style="font-weight: bold; font-size: 14px; color: #07C160;">阿拉丁</div>
                    <div style="font-size: 10px; color: #999;">微信指数</div>
                </a>
            </div>
        </div>
    """
    
    # 2. 动态打捞部分
    found_articles = []
    for url in FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:30]:
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
                            'summary': summary[:300] + "...",
                            'source': f"{feed.feed.get('title', '行业源')}"
                        })
        except: continue

    html += '<div style="background: white; padding: 20px; border-radius: 12px; border: 1px solid #e0e0e0;">'
    html += '<h2 style="font-size: 15px; color: #333; border-left: 4px solid #ff9800; padding-left: 10px; margin-bottom: 15px;">🗞️ 行业搬运文章 & 深度分析</h2>'
    
    if not found_articles:
        html += "<p style='text-align:center; padding: 30px; color: #999; font-size: 13px;'>暂未打捞到匹配资讯，请通过上方导航直达榜单。</p>"
    else:
        for art in found_articles:
            html += f"""
            <div style="border-bottom: 1px solid #f0f0f0; padding: 12px 0;">
                <h3 style="margin: 0 0 5px 0; font-size: 14px;"><a href="{art['link']}" style="color: #2c3e50; text-decoration: none;">{art['title']}</a></h3>
                <div style="font-size: 12px; color: #666;">{art['source']}</div>
            </div>
            """
    
    # 重点：确保这里所有标签和引号都完整闭合
    html += "</div></div>" 
    return html

def send_mail(content):
    sender = os.environ.get('EMAIL_USER')
    password = str(
