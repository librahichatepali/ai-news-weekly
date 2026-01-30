import os
import time
import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.header import Header

# --- 1. 配置区域 ---
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
RECIPIENT_EMAIL = "tanweilin1987@gmail.com"
SENDER_EMAIL = os.environ.get('EMAIL_USER')
SENDER_PASS = os.environ.get('EMAIL_PASS')

# 改用 RSS 订阅源，彻底杜绝 HTML 垃圾噪音
TARGET_SOURCES = [
    {"name": "Pocket Gamer RSS", "url": "https://www.pocketgamer.biz/feed/"},
    {"name": "MobileGamer.biz RSS", "url": "https://mobilegamer.biz/feed/"},
    {"name": "GameRefinery Blog", "url": "https://www.gamerefinery.com/feed/"}
]

# --- 2. AI 核心：修复换行符逻辑，提高识别率 ---
def ai_summarize(content, source_name):
    if not GEMINI_API_KEY: return "❌ 未配置 API KEY"
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    prompt = f"""
    你是资深游戏分析师。请从 {source_name} 的新闻列表中挑选 2-3 条今日要闻。
    重点：新游上线、融资、重大合作。用中文简述。
    若无实质新闻，请回复：暂无更新。
    
    新闻列表：
    {content[:12000]}
    """
    
    try:
        response = requests.post(api_url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=60)
        res_json = response.json()
        if "candidates" in res_json:
            return res_json["candidates"][0]["content"]["parts"][0]["text"]
        return "暂无更新"
    except Exception:
        return "AI 调用超时"

# --- 3. 邮件系统：修复 f-string 反斜杠错误 ---
def send_mail(content_list):
    combined_body = "".join(content_list)
    
    # 逻辑：如果结果为空，给出明确的系统状态
    status_msg = ""
    if not combined_body.strip():
        status_msg = '<p style="color:orange;">📡 探测完成：RSS 源链路正常，但今日 AI 判定无重大行业更新。</p>'

    # 修复：不再在 f-string {} 内直接使用 .replace('\n', '<br>') 以避免反斜杠报错
    html_layout = f"""
    <div style="font-family:sans-serif;max-width:650px;margin:auto;border:1px solid #eee;padding:20px;border-radius:10px;">
        <h2 style="color:#1a73e8;border-bottom:2px solid #1a73e8;">🎮 全球游戏雷达报</h2>
        {status_msg}
        <div style="line-height:1.6;">{combined_body}</div>
        <hr>
        <p style="font-size:12px;color:#999;text-align:center;">
            引擎: Gemini 1.5 Flash | 模式: RSS 纯净模式 | 时间: {time.strftime("%Y-%m-%d %H:%M")}
        </p>
    </div>
    """
    
    msg = MIMEText(html_layout, 'html', 'utf-8')
    msg['From'] = f"SmartRadar <{SENDER_EMAIL}>"
    msg['To'] = RECIPIENT_EMAIL
    msg['Subject'] = Header(f"📊 探测报告 - {time.strftime('%m-%d')}", 'utf-8')
    
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASS)
            server.sendmail(SENDER_EMAIL, [RECIPIENT_EMAIL], msg.as_string())
        print("✅ 邮件发送成功")
    except Exception as e:
        print(f"❌ 邮件异常: {e}")

# --- 4. 核心主逻辑 ---
if __name__ == "__main__":
    results = []
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    for src in TARGET_SOURCES:
        try:
            print(f"正在扫描: {src['name']}...")
            r = requests.get(src['url'], headers=headers, timeout=20)
            # RSS 这种 XML 结构极其纯净
            soup = BeautifulSoup(r.text, 'xml')
            items = soup.find_all('item')[:8]
            
            raw_text = ""
            for it in items:
                title = it.find('title').text if it.find('title') else ""
                raw_text += f"Title: {title}\n"
            
            if len(raw_text) > 20:
                summary = ai_summarize(raw_text, src['name'])
                if "暂无更新" not in summary:
                    # 先处理好换行符，再存入结果，避免 f-string 报错
                    formatted_summary = summary.replace('\n', '<br>')
                    section = f"""
                    <div style="background:#f4f7f9;padding:15px;border-radius:8px;margin-bottom:15px;">
                        <b style="color:#1a73e8;">📍 {src['name']}</b><br>{formatted_summary}
                    </div>
                    """
                    results.append(section)
        except Exception as e:
            print(f"错误 {src['name']}: {e}")
            
    send_mail(results)
