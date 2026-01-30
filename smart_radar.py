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

# 监控源增加精细化解析标签
TARGET_SOURCES = [
    {"name": "Pocket Gamer News", "url": "https://www.pocketgamer.biz/news/", "tag": "div", "class": "list-item"},
    {"name": "MobileGamer News", "url": "https://mobilegamer.biz/news/", "tag": "article"},
    {"name": "GameRefinery Blog", "url": "https://www.gamerefinery.com/blog/", "tag": "h2"}
]

# --- 2. AI 引擎 (多端点自动兼容) ---
def ai_summarize(content):
    if not GEMINI_API_KEY: return "❌ 密钥缺失"
    
    # 使用 v1beta 路径，这是目前支持最新的 flash 模型最稳健的路径
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    # 极度放宽的指令：要求 AI 只要看到新闻就总结
    prompt = (
        "你是一位游戏行业分析师。请从提供的网页片段中寻找任何关于移动游戏、超休闲游戏或行业趋势的新闻标题和简介。"
        "不要过滤日期，请直接总结出当前网页上最醒目的 3 条动态，并翻译成中文（简体）。内容如下：\n\n"
        f"{content[:9000]}"
    )
    
    try:
        response = requests.post(api_url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=45)
        res_json = response.json()
        if "candidates" in res_json:
            return res_json["candidates"][0]["content"]["parts"][0]["text"]
        return f"⚠️ AI 未能提取内容: {json.dumps(res_json.get('error', 'Unknown'))}"
    except Exception as e:
        return f"⚠️ 接口请求失败: {str(e)}"

# --- 3. 邮件发送系统 ---
def send_mail(content_list):
    full_body = "".join(content_list)
    if not full_body.strip():
        full_body = "<p style='color:red;'>🚨 探测失败：未能从目标源提取到有效文本，可能需要更换抓取库。</p>"

    html_layout = f"""
    <div style="font-family:sans-serif;max-width:700px;margin:auto;border:1px solid #eee;padding:25px;border-radius:12px;">
        <h2 style="color:#1a73e8;text-align:center;">📊 全球游戏情报·深度探测版</h2>
        <div style="line-height:1.8;">{full_body}</div>
        <div style="font-size:11px;color:#999;text-align:center;margin-top:30px;border-top:1px solid #f0f0f0;padding-top:15px;">
            验证模式：深度 HTML 扫描 | 时间：{time.strftime("%Y-%m-%d %H:%M")}
        </div>
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
        print("✅ 探测报告已发出")
    except Exception as e:
        print(f"❌ 邮件系统异常: {e}")

# --- 4. 深度抓取流程 ---
if __name__ == "__main__":
    results = []
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    for src in TARGET_SOURCES:
        try:
            print(f"正在深度探测: {src['name']}...")
            r = requests.get(src['url'], headers=headers, timeout=30)
            soup = BeautifulSoup(r.text, 'html.parser')
            
            # 尝试精细化提取内容，如果找不到标签则回退到全文提取
            items = soup.find_all(src.get('tag'), class_=src.get('class'))
            if items:
                probe_text = " ".join([i.get_text() for i in items[:15]])
            else:
                probe_text = soup.get_text(separator=' ', strip=True)
            
            summary = ai_summarize(probe_text)
            
            if "⚠️" not in summary and len(summary) > 20:
                section = f"""
                <div style="margin-bottom:20px;padding:15px;background:#f9f9f9;border-left:5px solid #1a73e8;">
                    <b style="color:#1a73e8;">📍 来源：{src['name']}</b><br>
                    <div style="margin-top:10px;font-size:14px;">{summary.replace('\n', '<br>')}</div>
                </div>
                """
                results.append(section)
        except Exception as e:
            print(f"跳过 {src['name']}: {e}")
            continue
        
    send_mail(results)
