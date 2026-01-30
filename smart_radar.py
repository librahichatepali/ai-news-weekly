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

# 监控源：聚焦全球主流移动游戏媒体
TARGET_SOURCES = [
    {"name": "Pocket Gamer News", "url": "https://www.pocketgamer.biz/news/"},
    {"name": "GameRefinery Blog", "url": "https://www.gamerefinery.com/blog/"},
    {"name": "MobileGamer.biz", "url": "https://mobilegamer.biz/news/"}
]

# --- 2. AI 核心引擎 (解决 404 与 v1beta 路径兼容) ---
def ai_summarize(content):
    if not GEMINI_API_KEY: return "❌ 错误：未配置 Key"
    
    # 锁定 v1beta 路径，这是目前最稳健的调用方式
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    prompt = (
        "你是一位移动游戏分析师。请从下文中总结 3 条最新的全球行业动态。"
        "要求：必须使用中文，每条动态包含标题和简短说明。"
        f"\n\n待分析网页文本：\n{content[:8000]}"
    )
    
    try:
        response = requests.post(api_url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=60)
        res_json = response.json()
        if "candidates" in res_json:
            return res_json["candidates"][0]["content"]["parts"][0]["text"]
        return "⚠️ AI 未能从内容中提取出有效动态"
    except Exception as e:
        return f"⚠️ API 请求异常: {str(e)}"

# --- 3. 邮件发送系统 (修复 f-string 语法错误) ---
def send_mail(content_list):
    # 修复 image_b84199: 预先合并内容，避免在 f-string 中处理反斜杠
    combined_body = "".join(content_list)
    
    if not combined_body.strip():
        combined_body = "<p style='color:orange;'>今日探测完成，但目标源未发现足够长度的动态摘要。</p>"

    html_layout = f"""
    <div style="font-family:sans-serif;max-width:700px;margin:auto;border:1px solid #ddd;padding:25px;border-radius:15px;">
        <h2 style="color:#1a73e8;text-align:center;border-bottom:3px solid #1a73e8;padding-bottom:12px;">🌍 全球游戏动态·探测报告</h2>
        <div style="line-height:1.7;color:#333;">{combined_body}</div>
        <div style="font-size:12px;color:#999;text-align:center;margin-top:30px;border-top:1px solid #eee;padding-top:15px;">
            验证状态：深度文本清洗 | 引擎：Gemini 1.5 Flash | 时间：{time.strftime("%Y-%m-%d %H:%M")}
        </div>
    </div>
    """
    msg = MIMEText(html_layout, 'html', 'utf-8')
    msg['From'] = f"SmartRadar <{SENDER_EMAIL}>"
    msg['To'] = RECIPIENT_EMAIL
    msg['Subject'] = Header(f"📊 全球趋势探测 - {time.strftime('%m-%d')}", 'utf-8')
    
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASS)
            server.sendmail(SENDER_EMAIL, [RECIPIENT_EMAIL], msg.as_string())
        print("✅ 报告已送达邮件")
    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")

# --- 4. 深度提取流程 ---
if __name__ == "__main__":
    results = []
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    for src in TARGET_SOURCES:
        try:
            print(f"正在分析: {src['name']}...")
            r = requests.get(src['url'], headers=headers, timeout=25)
            soup = BeautifulSoup(r.text, 'html.parser')
            
            # 强力文本清洗：剔除干扰标签，防止 AI 获取到垃圾信息
            for noise in soup(['script', 'style', 'nav', 'footer', 'header']):
                noise.decompose()
            
            clean_text = soup.get_text(separator=' ', strip=True)
            summary = ai_summarize(clean_text)
            
            if "⚠️" not in summary and len(summary) > 40:
                # 修复语法错误：在外部完成 HTML 换行转换
                safe_summary = summary.replace('\n', '<br>')
                section = f"""
                <div style="margin-bottom:20px;padding:15px;background:#fcfcfc;border-left:5px solid #1a73e8;">
                    <b style="color:#1a73e8;">📍 来源：{src['name']}</b><br>
                    <div style="margin-top:10px;font-size:14px;">{safe_summary}</div>
                </div>
                """
                results.append(section)
        except Exception as e:
            print(f"跳过 {src['name']}: {e}")
            continue
            
    send_mail(results)
