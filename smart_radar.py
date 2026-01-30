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

# 监控外网源：无拦截且内容质量高
TARGET_SOURCES = [
    {"name": "Pocket Gamer", "url": "https://www.pocketgamer.biz/news/"},
    {"name": "GameRefinery", "url": "https://www.gamerefinery.com/blog/"},
    {"name": "MobileGamer.biz", "url": "https://mobilegamer.biz/"}
]

# --- 2. AI 引擎 (修复 404 模型未找到报错) ---
def ai_summarize(content):
    if not GEMINI_API_KEY: return "❌ 错误：未配置 Key"
    
    # 核心修复：锁定 v1beta 版本，并将模型完整路径设为 models/gemini-1.5-flash
    # 这是解决 image_b7d498 报错的关键
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [{
            "parts": [{
                "text": f"你是一位全球移动游戏分析师。请分析下文中 2026年1月 的小游戏或超休闲游戏趋势，并用中文简要总结 3 个重点：\n\n{content[:6000]}"
            }]
        }]
    }

    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=60)
        res_json = response.json()
        
        if "candidates" in res_json:
            return res_json["candidates"][0]["content"]["parts"][0]["text"]
        
        # 如果 v1beta 报错，自动尝试 v1 稳定版路径
        alt_url = api_url.replace("v1beta", "v1")
        response = requests.post(alt_url, headers=headers, json=payload, timeout=60)
        res_json = response.json()
        
        if "candidates" in res_json:
            return res_json["candidates"][0]["content"]["parts"][0]["text"]
        else:
            return f"⚠️ AI 接口返回异常: {json.dumps(res_json.get('error', 'Unknown Error'))}"
            
    except Exception as e:
        return f"⚠️ 接口请求失败: {str(e)}"

# --- 3. 邮件发送系统 ---
def send_mail(content_list):
    full_body = "".join(content_list)
    if not full_body.strip():
        full_body = "<p style='color:orange;'>今日扫描完成，暂无符合条件的深度动态。</p>"

    html_layout = f"""
    <div style="font-family:sans-serif;max-width:750px;margin:auto;border:1px solid #ddd;padding:30px;border-radius:15px;">
        <h2 style="color:#1a73e8;text-align:center;border-bottom:4px solid #1a73e8;padding-bottom:12px;">🌍 全球小游戏·趋势周报</h2>
        <div style="line-height:1.7;color:#333;">{full_body}</div>
        <div style="font-size:12px;color:#999;text-align:center;margin-top:40px;border-top:1px solid #eee;padding-top:20px;">
            情报来源：全球顶级移动媒体 | 引擎：Gemini 1.5 Flash | 时间：{time.strftime("%Y-%m-%d %H:%M")}
        </div>
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
        print("✅ 报告已送达邮箱")
    except Exception as e:
        print(f"❌ 邮件系统异常: {e}")

# --- 4. 主流程 ---
if __name__ == "__main__":
    results = []
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    for src in TARGET_SOURCES:
        try:
            print(f"正在扫描: {src['name']}...")
            r = requests.get(src['url'], headers=headers, timeout=20)
            # 提取纯文本
            text = BeautifulSoup(r.text, 'html.parser').get_text(separator=' ', strip=True)
            summary = ai_summarize(text)
            
            if "⚠️" not in summary and len(summary) > 50:
                clean_summary = summary.replace('\n', '<br>')
                section = f"""
                <div style="margin-bottom:25px;padding:20px;background:#fcfcfc;border-left:6px solid #1a73e8;border-radius:0 8px 8px 0;">
                    <b style="color:#1a73e8;font-size:16px;">📍 来源：{src['name']}</b><br>
                    <div style="margin-top:12px;font-size:15px;">{clean_summary}</div>
                </div>
                """
                results.append(section)
        except: continue
        
    send_mail(results)
