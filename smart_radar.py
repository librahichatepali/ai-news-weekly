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

# --- 2. AI 核心引擎 (锁定 v1beta 路径) ---
def ai_summarize(content):
    if not GEMINI_API_KEY: return "❌ 错误：未配置 Key"
    
    # 使用目前最稳定的 v1beta 路径，避免 404 错误
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    prompt = (
        "你是一位移动游戏分析师。请从提供的网页文本中总结 3 条最新的行业动态。"
        "要求：必须使用中文回复。如果内容不完整，请基于片段提供最有价值的信息。"
        f"\n\n待分析文本：\n{content[:9000]}"
    )
    
    try:
        response = requests.post(api_url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=60)
        res_json = response.json()
        if "candidates" in res_json:
            return res_json["candidates"][0]["content"]["parts"][0]["text"]
        return "⚠️ AI 未发现明确动态"
    except Exception as e:
        return f"⚠️ API 请求异常: {str(e)}"

# --- 3. 邮件发送系统 (彻底修复 f-string 反斜杠报错) ---
def send_mail(content_list):
    # 核心修复点：预先合并内容，避免在 f-string 内部进行字符串处理
    combined_body = "".join(content_list)
    
    if not combined_body.strip():
        combined_body = "<p style='color:orange;'>今日探测完成，但目标网站结构可能已变动，未能提取到有效动态。</p>"

    html_layout = f"""
    <div style="font-family:sans-serif;max-width:700px;margin:auto;border:1px solid #ddd;padding:30px;border-radius:15px;">
        <h2 style="color:#1a73e8;text-align:center;border-bottom:4px solid #1a73e8;padding-bottom:12px;">🌍 全球游戏动态·深度探测</h2>
        <div style="line-height:1.7;color:#333;">{combined_body}</div>
        <div style="font-size:12px;color:#999;text-align:center;margin-top:40px;border-top:1px solid #eee;padding-top:20px;">
            验证状态：深度文本清洗 | 引擎：Gemini 1.5 Flash | 时间：{time.strftime("%Y-%m-%d %H:%M")}
        </div>
    </div>
    """
    msg = MIMEText(html_layout, 'html', 'utf-8')
    msg['From'] = f"SmartRadar <{SENDER_EMAIL}>"
    msg['To'] = RECIPIENT_EMAIL
    msg['Subject'] = Header(f"📊 趋势探测报告 - {time.strftime('%m-%d')}", 'utf-8')
    
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASS)
            server.sendmail(SENDER_EMAIL, [RECIPIENT_EMAIL], msg.as_string())
        print("✅ 报告已成功发出")
    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")

# --- 4. 强力提取流程 (解决解析噪音) ---
if __name__ == "__main__":
    results = []
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    for src in TARGET_SOURCES:
        try:
            print(f"正在分析: {src['name']}...")
            r = requests.get(src['url'], headers=headers, timeout=25)
            soup = BeautifulSoup(r.text, 'html.parser')
            
            # 物理剔除干扰：防止 AI 抓取到垃圾信息的核心逻辑
            for noise in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
                noise.decompose()
            
            clean_text = soup.get_text(separator=' ', strip=True)
            summary = ai_summarize(clean_text)
            
            if "⚠️" not in summary and len(summary) > 40:
                # 修复语法错误：在进入 f-string 前完成换行符转换
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
