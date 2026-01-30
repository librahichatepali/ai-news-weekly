import os
import time
import requests
import json
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.header import Header

# --- 1. 配置区域 ---
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
RECIPIENT_EMAIL = "tanweilin1987@gmail.com"
SENDER_EMAIL = os.environ.get('EMAIL_USER')
SENDER_PASS = os.environ.get('EMAIL_PASS')

# 切换为外网源：更易抓取，内容深度更高
TARGET_SOURCES = [
    {"name": "Pocket Gamer (Global)", "url": "https://www.pocketgamer.biz/news/"},
    {"name": "GameRefinery (Analysis)", "url": "https://www.gamerefinery.com/blog/"},
    {"name": "Mobilegamer.biz", "url": "https://mobilegamer.biz/"}
]

# --- 2. AI 引擎 (模型标识符兼容修复) ---
def ai_summarize(content):
    if not GEMINI_API_KEY: return "❌ 错误：未配置 Key"
    
    # 修复点：使用 latest 标识符并尝试 v1beta1 备选路径以应对 Google 区域调整
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [{"parts": [{"text": f"You are a gaming analyst. Extract mini-game or hypercasual trends for Jan 2026 from this content. Provide summary in Chinese (Simplified):\n\n{content[:5000]}"}]}]
    }

    try:
        response = requests.post(api_url, headers=headers, data=json.dumps(payload), timeout=60)
        res_json = response.json()
        if "candidates" in res_json:
            return res_json["candidates"][0]["content"]["parts"][0]["text"]
        else:
            # 自动降级尝试 v1 路径
            alt_url = api_url.replace("v1beta", "v1")
            response = requests.post(alt_url, headers=headers, data=json.dumps(payload), timeout=60)
            res_json = response.json()
            return res_json["candidates"][0]["content"]["parts"][0]["text"] if "candidates" in res_json else f"⚠️ AI 响应异常: {json.dumps(res_json)}"
    except Exception as e:
        return f"⚠️ 接口请求失败: {str(e)}"

# --- 3. 邮件发送系统 ---
def send_mail(content_list):
    full_body = "".join(content_list)
    if not full_body.strip():
        full_body = "<p style='color:orange;'>今日扫描完成，但外网监控源暂未发现符合条件的行业动态。</p>"

    html_layout = f"""
    <div style="font-family:sans-serif;max-width:700px;margin:auto;border:1px solid #eee;padding:25px;border-radius:12px;">
        <h2 style="color:#1a73e8;border-bottom:3px solid #1a73e8;padding-bottom:10px;text-align:center;">🌍 全球小游戏趋势内参</h2>
        <div style="line-height:1.8;color:#333;">{full_body}</div>
        <div style="font-size:11px;color:#aaa;text-align:center;margin-top:30px;border-top:1px solid #f0f0f0;padding-top:15px;">数据源：PocketGamer/GameRefinery | 时间：{time.strftime("%Y-%m-%d %H:%M")}</div>
    </div>
    """
    msg = MIMEText(html_layout, 'html', 'utf-8')
    msg['From'] = f"SmartRadar <{SENDER_EMAIL}>"
    msg['To'] = RECIPIENT_EMAIL
    msg['Subject'] = Header(f"📊 全球趋势报告 - {time.strftime('%m-%d')}", 'utf-8')
    
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASS)
            server.sendmail(SENDER_EMAIL, [RECIPIENT_EMAIL], msg.as_string())
        print("✅ 邮件已成功送达")
    except Exception as e:
        print(f"❌ 邮件系统异常: {e}")

# --- 4. 主流程 ---
if __name__ == "__main__":
    results = []
    # 此时请求外网媒体，不再会有被屏蔽的问题
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    for src in TARGET_SOURCES:
        try:
            print(f"正在扫描外网媒体: {src['name']}...")
            r = requests.get(src['url'], headers=headers, timeout=20)
            text = BeautifulSoup(r.text, 'html.parser').get_text(separator=' ', strip=True)
            summary = ai_summarize(text)
            
            if len(summary) > 30:
                clean_summary = summary.replace('\n', '<br>')
                section = f"""
                <div style="margin-bottom:20px;padding:15px;background:#f9f9f9;border-left:5px solid #1a73e8;">
                    <b style="color:#1a73e8;">📍 来源：{src['name']}</b><br>
                    <div style="margin-top:10px;font-size:14px;">{clean_summary}</div>
                </div>
                """
                results.append(section)
        except: continue
        
    send_mail(results)
