import os
import time
import requests
import json
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.header import Header

# --- 1. 环境配置 ---
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
RECIPIENT_EMAIL = "tanweilin1987@gmail.com"
SENDER_EMAIL = os.environ.get('EMAIL_USER')
SENDER_PASS = os.environ.get('EMAIL_PASS')

# 目标媒体：转向全球顶级移动游戏站点，解决国内源屏蔽问题
TARGET_SOURCES = [
    {"name": "Pocket Gamer (Global)", "url": "https://www.pocketgamer.biz/news/"},
    {"name": "GameRefinery (Analysis)", "url": "https://www.gamerefinery.com/blog/"},
    {"name": "MobileGamer.biz", "url": "https://mobilegamer.biz/"}
]

# --- 2. AI 引擎 (修复 404 标识符报错) ---
def ai_summarize(content):
    if not GEMINI_API_KEY: return "❌ 错误：未配置 API KEY"
    
    # 修复核心：使用 v1beta 路径，这是目前支持 gemini-1.5-flash 最稳定的端点
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    headers = {'Content-Type': 'application/json'}
    # 提示词要求：抓取外网内容并用中文总结
    prompt = f"""
    你是一位全球游戏行业分析师。请分析下文中关于 2026年1月 的移动游戏、超休闲游戏或小游戏趋势。
    要求：用中文（简体）提炼 3 个核心干货点。
    原文内容：
    {content[:5000]}
    """
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }

    try:
        response = requests.post(api_url, headers=headers, data=json.dumps(payload), timeout=60)
        res_json = response.json()
        if "candidates" in res_json:
            return res_json["candidates"][0]["content"]["parts"][0]["text"]
        else:
            # 捕获并返回具体的 API 错误信息
            err_msg = res_json.get('error', {}).get('message', '未知接口错误')
            return f"⚠️ AI 响应异常: {err_msg}"
    except Exception as e:
        return f"⚠️ 请求失败: {str(e)}"

# --- 3. 邮件系统 ---
def send_mail(content_list):
    full_body = "".join(content_list)
    if not full_body.strip():
        full_body = "<p style='color:orange;'>今日扫描完成，但在外网源中暂未发现深度趋势分析。</p>"

    html_layout = f"""
    <div style="font-family:sans-serif;max-width:700px;margin:auto;border:1px solid #ddd;padding:25px;border-radius:12px;">
        <h2 style="color:#1a73e8;text-align:center;border-bottom:3px solid #1a73e8;padding-bottom:10px;">🌍 全球游戏趋势内参</h2>
        <div style="line-height:1.7;">{full_body}</div>
        <div style="font-size:11px;color:#aaa;text-align:center;margin-top:30px;border-top:1px solid #eee;padding-top:15px;">
            情报来源：全球顶级移动媒体 | 时间：{time.strftime("%Y-%m-%d %H:%M")}
        </div>
    </div>
    """
    msg = MIMEText(html_layout, 'html', 'utf-8')
    msg['From'] = f"SmartRadar <{SENDER_EMAIL}>"
    msg['To'] = RECIPIENT_EMAIL
    msg['Subject'] = Header(f"📊 全球趋势情报报告 - {time.strftime('%m-%d')}", 'utf-8')
    
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASS)
            server.sendmail(SENDER_EMAIL, [RECIPIENT_EMAIL], msg.as_string())
        print("✅ 邮件已成功发出")
    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")

# --- 4. 运行主函数 ---
if __name__ == "__main__":
    results = []
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    for src in TARGET_SOURCES:
        try:
            print(f"正在扫描: {src['name']}...")
            r = requests.get(src['url'], headers=headers, timeout=20)
            text = BeautifulSoup(r.text, 'html.parser').get_text(separator=' ', strip=True)
            summary = ai_summarize(text)
            
            if len(summary) > 40:
                clean_summary = summary.replace('\n', '<br>')
                section = f"""
                <div style="margin-bottom:20px;padding:15px;background:#f9f9f9;border-left:5px solid #1a73e8;">
                    <b style="color:#1a73e8;">📍 来源：{src['name']}</b><br>
                    <div style="margin-top:10px;">{clean_summary}</div>
                </div>
                """
                results.append(section)
        except Exception as e:
            print(f"⚠️ 无法访问 {src['name']}: {e}")
            continue
        
    send_mail(results)
