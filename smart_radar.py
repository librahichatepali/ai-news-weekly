import os
import time
import requests
import json
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.header import Header

# --- 1. 核心配置 ---
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
RECIPIENT_EMAIL = "tanweilin1987@gmail.com"
SENDER_EMAIL = os.environ.get('EMAIL_USER')
SENDER_PASS = os.environ.get('EMAIL_PASS')

TARGET_SOURCES = [
    {"name": "游戏日报", "url": "https://www.gamelook.com.cn/category/mini-game"},
    {"name": "游戏陀螺", "url": "https://www.youxituoluo.com/tag/%E5%B0%8F%E6%B8%B8%E6%88%8F"},
    {"name": "小红书-她按开始键", "url": "https://www.xiaohongshu.com/user/profile/5df0a6990000000001000695"},
    {"name": "DataEye报告", "url": "https://www.dataeye.com/report"}
]

# --- 2. AI 原生请求引擎 (彻底跳过 v1beta 路径) ---
def ai_summarize(content):
    if not GEMINI_API_KEY:
        return "❌ 错误：未配置 GEMINI_API_KEY"
    
    # 核心修复：直接使用 v1 稳定版 REST API 地址
    api_url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [{
            "parts": [{
                "text": f"你是一位游戏猎头。请提炼以下内容中 2026年1月 的小游戏行业干货：\n\n{content[:4000]}"
            }]
        }]
    }

    try:
        response = requests.post(api_url, headers=headers, data=json.dumps(payload), timeout=60)
        res_json = response.json()
        # 提取 AI 回复文本
        if "candidates" in res_json:
            return res_json["candidates"][0]["content"]["parts"][0]["text"]
        else:
            return f"⚠️ AI 响应异常: {json.dumps(res_json)}"
    except Exception as e:
        return f"⚠️ 接口请求失败: {str(e)}"

# --- 3. 邮件发送系统 (结构加固) ---
def send_mail(content_list):
    full_body = "".join(content_list)
    if not full_body.strip():
        full_body = "<p style='color:orange;'>今日扫描完成，但暂未发现匹配的深度动态。</p>"

    html_header = '<div style="font-family:sans-serif;max-width:700px;margin:auto;border:1px solid #eee;padding:25px;border-radius:12px;">'
    html_title = '<h2 style="color:#1a73e8;border-bottom:3px solid #1a73e8;padding-bottom:10px;text-align:center;">🛡️ 小游戏·深度情报雷达</h2>'
    curr_time = time.strftime("%Y-%m-%d %H:%M")
    html_footer = f'<div style="font-size:11px;color:#aaa;text-align:center;margin-top:30px;border-top:1px solid #f0f0f0;padding-top:15px;">监控时效：30日内 | 时间：{curr_time}</div></div>'
    
    msg = MIMEText(html_header + html_title + full_body + html_footer, 'html', 'utf-8')
    msg['From'] = f"SmartRadar <{SENDER_EMAIL}>"
    msg['To'] = RECIPIENT_EMAIL
    msg['Subject'] = Header(f"📊 小游戏趋势内参 - {time.strftime('%m-%d')}", 'utf-8')
    
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASS)
            server.sendmail(SENDER_EMAIL, [RECIPIENT_EMAIL], msg.as_string())
        print("✅ 邮件已发送")
    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")

# --- 4. 执行流程 ---
if __name__ == "__main__":
    results = []
    # 模拟真实浏览器请求，防止被封禁
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    for src in TARGET_SOURCES:
        try:
            print(f"正在扫描: {src['name']}...")
            r = requests.get(src['url'], headers=headers, timeout=20)
            # 抓取纯文本并提交给 AI
            text = BeautifulSoup(r.text, 'html.parser').get_text(separator=' ', strip=True)
            summary = ai_summarize(text)
            
            if len(summary) > 30:
                # 预处理 AI 返回的换行符
                safe_summary = summary.replace('\n', '<br>')
                section = f"""
                <div style="margin-bottom:20px;padding:15px;background:#f9f9f9;border-left:5px solid #1a73e8;">
                    <b style="color:#1a73e8;">📍 来源：{src['name']}</b><br>
                    <div style="margin-top:10px;font-size:14px;">{safe_summary}</div>
                </div>
                """
                results.append(section)
        except Exception as e:
            print(f"⚠️ {src['name']} 访问受阻: {e}")
            continue
        
    send_mail(results)
