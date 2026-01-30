import os
import time
import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.header import Header

# --- 1. 基础配置 ---
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
RECIPIENT_EMAIL = "tanweilin1987@gmail.com"
SENDER_EMAIL = os.environ.get('EMAIL_USER')
SENDER_PASS = os.environ.get('EMAIL_PASS')

# 监控的数据源
TARGET_SOURCES = [
    {"name": "Pocket Gamer (移动游戏)", "url": "https://www.pocketgamer.biz/feed/"},
    {"name": "MobileGamer.biz (深度专栏)", "url": "https://mobilegamer.biz/feed/"},
    {"name": "GameRefinery (市场趋势)", "url": "https://www.gamerefinery.com/feed/"}
]

# --- 2. 业务聚焦型 AI 函数 ---
def ai_summarize(content, source_name):
    if not GEMINI_API_KEY: return ""
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    # 调整后的 Prompt：聚焦关键词，不再“挑剔”
    prompt = f"""
    任务：你是专业游戏市场情报员。请从以下 {source_name} 的新闻中提取核心价值。
    
    核心关注点（优先提取）：
    1. 小游戏(Mini-games/H5/Instant Games)的相关动态。
    2. 热销榜、排行榜(Top Grossing/Charts/Ranking)的变动。
    3. 市场大盘趋势、竞品重要数据。
    
    要求：
    1. 即使内容不完全符合上述点，也要翻译为中文。
    2. 禁止回答“今日无深度资讯”，必须输出至少 3-5 条摘要。
    3. 格式：[标签] 简要内容描述
    
    待处理内容：
    {content}
    """
    
    try:
        response = requests.post(api_url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=60)
        res_json = response.json()
        if "candidates" in res_json:
            return res_json["candidates"][0]["content"]["parts"][0]["text"].strip()
        return ""
    except Exception as e:
        print(f"AI 接口异常: {e}")
        return ""

# --- 3. 邮件发送系统：修复保底变量名 ---
def send_mail(content_list, backup_titles):
    ai_output = "".join(content_list).strip()
    
    # 修复 image_9ab91c 中提到的 NameError 变量名错误
    if not ai_output:
        # 确保使用正确的变量名 backup_titles
        backup_html = "<ul>" + "".join([f"<li>{t}</li>" for t in backup_titles]) + "</ul>"
        main_body = f"""
        <div style="padding:15px; background:#fff3cd; color:#856404; border-radius:8px; border:1px solid #ffeeba;">
            ⚠️ AI 未产出摘要，以下为直接抓取的原始标题：<br>{backup_html}
        </div>
        """
    else:
        main_body = ai_output

    html_layout = f"""
    <div style="font-family:sans-serif; max-width:650px; margin:auto; border:1px solid #eee; padding:25px; border-radius:15px; background:#fff;">
        <h2 style="color:#1a73e8; text-align:center; border-bottom:2px solid #1a73e8; padding-bottom:10px;">📊 全球游戏·情报雷达</h2>
        <div style="line-height:1.8; color:#333;">{main_body}</div>
        <div style="font-size:12px; color:#aaa; text-align:center; margin-top:30px; border-top:1px solid #f0f0f0; padding-top:15px;">
            模式: 聚焦小游戏/排行榜 | 时间: {time.strftime("%Y-%m-%d %H:%M")}
        </div>
    </div>
    """
    
    msg = MIMEText(html_layout, 'html', 'utf-8')
    msg['From'] = f"SmartRadar <{SENDER_EMAIL}>"
    msg['To'] = RECIPIENT_EMAIL
    msg['Subject'] = Header(f"🎮 市场动态简报 - {time.strftime('%m-%d')}", 'utf-8')
    
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASS)
            server.sendmail(SENDER_EMAIL, [RECIPIENT_EMAIL], msg.as_string())
        print("✅ 邮件已成功发出")
    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")

# --- 4. 运行逻辑 ---
if __name__ == "__main__":
    final_results = []
    all
