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

# 转向全球媒体：更开放、无反爬，且是小游戏创新的源头
TARGET_SOURCES = [
    {"name": "Pocket Gamer (Global)", "url": "https://www.pocketgamer.biz/news/"},
    {"name": "GameRefinery (Dev Blog)", "url": "https://www.gamerefinery.com/blog/"},
    {"name": "MobileGamer.biz", "url": "https://mobilegamer.biz/news/"}
]

# --- 2. AI 引擎 (修复 404 标识符报错) ---
def ai_summarize(content):
    if not GEMINI_API_KEY: return "❌ 错误：密钥未配置"
    
    # 修复点：使用 v1beta 路径并锁定正式模型名，这是目前最稳定的组合
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    headers = {'Content-Type': 'application/json'}
    # 提示词要求 AI 将外网干货翻译为中文，方便你阅读
    prompt = (
        "你是一位资深游戏行业分析师。请从下文中挖掘 2026年1月 的移动游戏、超休闲游戏或小游戏趋势。"
        "请用中文提供简洁的分析报告，包含：1. 核心趋势；2. 值得关注的新品或数据。内容如下：\n\n"
        f"{content[:6000]}"
    )
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }

    try:
        response = requests.post(api_url, headers=headers, data=json.dumps(payload), timeout=60)
        res_json = response.json()
        if "candidates" in res_json:
            return res_json["candidates"][0]["content"]["parts"][0]["text"]
        else:
            return f"⚠️ API 异常响应: {res_json.get('error', {}).get('message', '未知错误')}"
    except Exception as e:
        return f"⚠️ 接口请求失败: {str(e)}"

# --- 3. 邮件发送系统 ---
def send_mail(content_list):
    full_body = "".join(content_list)
    if not full_body.strip():
        full_body = "<p style='color:orange;'>今日扫描完成，但在外网监控源中暂未发现深度分析内容。</p>"

    html_layout = f"""
    <div style="font-family:sans-serif;max-width:750px;margin:auto;border:1px solid #ddd;padding:30px;border-radius:15px;box-shadow:0 4px 15px rgba(0,0,0,0.1);">
        <h2 style="color:#1a73e8;border-bottom:4px solid #1a73e8;padding-bottom:12px;text-align:center;">🌍 全球小游戏·趋势周报</h2>
        <div style="line-height:1.7;color:#444;">{full_body}</div>
        <div style="font-size:12px;color:#999;text-align:center;margin-top:40px;border-top:1px solid #eee;padding-top:20px;">
            情报来源：全球顶级移动媒体 | 引擎：Gemini 1.5 Pro | 时间：{time.strftime("%Y-%m-%d %H:%M")}
        </div>
    </div>
    """
    msg = MIMEText(html_layout, 'html', 'utf-8')
    msg['From'] = f"SmartRadar <{SENDER_EMAIL}>"
    msg['To'] = RECIPIENT_EMAIL
    msg['Subject'] = Header(f"📊 全球游戏情报报告 - {time.strftime('%m-%d')}", 'utf-8')
    
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASS)
            server.sendmail(SENDER_EMAIL, [RECIPIENT_EMAIL], msg.as_string())
        print("✅ 邮件发送成功")
    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")

# --- 4. 运行主函数 ---
if __name__ == "__main__":
    results = []
    # 访问国际媒体，无需担心 IP 封禁
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    for src in TARGET_SOURCES:
        try:
            print(f"正在扫描: {src['name']}...")
            r = requests.get(src['url'], headers=headers, timeout=20)
            soup = BeautifulSoup(r.text, 'html.parser')
            # 抓取主要新闻区域的文本
            text = soup.get_text(separator=' ', strip=True)
            summary = ai_summarize(text)
            
            if len(summary) > 50:
                clean_summary = summary.replace('\n', '<br>')
                section = f"""
                <div style="margin-bottom:25px;padding:20px;background:#fcfcfc;border-left:6px solid #1a73e8;border-radius:0 8px 8px 0;">
                    <b style="color:#1a73e8;font-size:16px;">📍 来源：{src['name']}</b><br>
                    <div style="margin-top:12px;font-size:15px;color:#222;">{clean_summary}</div>
                </div>
                """
                results.append(section)
        except Exception as e:
            print(f"⚠️ 无法访问 {src['name']}: {e}")
            continue
        
    send_mail(results)
