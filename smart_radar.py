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

# 依然使用外网优质源，确保 GitHub Actions 抓取无阻碍
TARGET_SOURCES = [
    {"name": "Pocket Gamer", "url": "https://www.pocketgamer.biz/news/"},
    {"name": "GameRefinery", "url": "https://www.gamerefinery.com/blog/"},
    {"name": "MobileGamer.biz", "url": "https://mobilegamer.biz/"}
]

# --- 2. AI 引擎 (采用已验证的 v1beta 路径) ---
def ai_summarize(content):
    if not GEMINI_API_KEY: return "❌ 错误：未配置 Key"
    
    # 锁定已跑通的 v1beta 路径，避免 404
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    headers = {'Content-Type': 'application/json'}
    
    # 核心变动：放宽时间限制，要求 AI 提取任何“最新”或“近期”的重要情报
    prompt = (
        "你是一位全球移动游戏分析师。请从下文中提取【最新】的游戏动态、行业趋势或爆款数据。"
        "不要局限于特定月份，只要是网页中提到的核心干货即可。"
        "请用中文提供 3 条简洁的分析。内容如下：\n\n"
        f"{content[:8000]}"
    )
    
    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=60)
        res_json = response.json()
        if "candidates" in res_json:
            return res_json["candidates"][0]["content"]["parts"][0]["text"]
        return f"⚠️ API 异常: {json.dumps(res_json.get('error', '未知错误'))}"
    except Exception as e:
        return f"⚠️ 请求失败: {str(e)}"

# --- 3. 邮件发送系统 ---
def send_mail(content_list):
    full_body = "".join(content_list)
    if not full_body.strip():
        full_body = "<p style='color:orange;'>⚠️ 今日未抓取到有效摘要，请检查目标源 HTML 结构。</p>"

    html_layout = f"""
    <div style="font-family:sans-serif;max-width:750px;margin:auto;border:1px solid #ddd;padding:30px;border-radius:15px;">
        <h2 style="color:#1a73e8;text-align:center;border-bottom:4px solid #1a73e8;padding-bottom:12px;">🌍 全球游戏动态·功能验证</h2>
        <div style="line-height:1.7;color:#333;">{full_body}</div>
        <div style="font-size:12px;color:#999;text-align:center;margin-top:40px;border-top:1px solid #eee;padding-top:20px;">
            情报来源：全球媒体 | 验证状态：放宽时间限制 | 时间：{time.strftime("%Y-%m-%d %H:%M")}
        </div>
    </div>
    """
    msg = MIMEText(html_layout, 'html', 'utf-8')
    msg['From'] = f"SmartRadar <{SENDER_EMAIL}>"
    msg['To'] = RECIPIENT_EMAIL
    msg['Subject'] = Header(f"📊 全球游戏情报测试 - {time.strftime('%m-%d')}", 'utf-8')
    
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASS)
            server.sendmail(SENDER_EMAIL, [RECIPIENT_EMAIL], msg.as_string())
        print("✅ 验证邮件已发送")
    except Exception as e:
        print(f"❌ 邮件系统异常: {e}")

# --- 4. 运行流程 ---
if __name__ == "__main__":
    results = []
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    for src in TARGET_SOURCES:
        try:
            print(f"正在扫描: {src['name']}...")
            r = requests.get(src['url'], headers=headers, timeout=20)
            # 抓取整个页面的文本，不仅限于新闻列表，增加成功率
            text = BeautifulSoup(r.text, 'html.parser').get_text(separator=' ', strip=True)
            summary = ai_summarize(text)
            
            if "⚠️" not in summary and len(summary) > 30:
                clean_summary = summary.replace('\n', '<br>')
                section = f"""
                <div style="margin-bottom:25px;padding:20px;background:#fcfcfc;border-left:6px solid #1a73e8;">
                    <b style="color:#1a73e8;font-size:16px;">📍 来源：{src['name']}</b><br>
                    <div style="margin-top:12px;font-size:15px;">{clean_summary}</div>
                </div>
                """
                results.append(section)
        except Exception as e:
            print(f"扫描跳过 {src['name']}: {e}")
            continue
        
    send_mail(results)
