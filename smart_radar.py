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

# 精选外网源，并加入多级解析策略
TARGET_SOURCES = [
    {"name": "Pocket Gamer News", "url": "https://www.pocketgamer.biz/news/"},
    {"name": "GameRefinery Blog", "url": "https://www.gamerefinery.com/blog/"},
    {"name": "MobileGamer.biz", "url": "https://mobilegamer.biz/news/"}
]

# --- 2. AI 核心引擎 (解决 v1beta 兼容性与 404) ---
def ai_summarize(content):
    if not GEMINI_API_KEY: return "❌ 错误：未配置 Key"
    
    # 使用 v1beta 路径，这是目前最稳定的 gemini-1.5-flash 端点
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    # 极为宽松的 Prompt：要求 AI 提取任何新闻干货
    prompt = (
        "你是一位全球移动游戏分析师。请从提供的网页文本中，提取并总结 3 条最新的行业动态或游戏趋势。"
        "必须使用中文回复。如果文本中有关于新游戏发布、融资或市场数据的消息，请优先提取。"
        f"\n\n待分析内容：\n{content[:9000]}"
    )
    
    headers = {'Content-Type': 'application/json'}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=60)
        res_json = response.json()
        if "candidates" in res_json:
            return res_json["candidates"][0]["content"]["parts"][0]["text"]
        return f"⚠️ AI 接口返回异常: {json.dumps(res_json.get('error', 'Unknown'))}"
    except Exception as e:
        return f"⚠️ 接口请求失败: {str(e)}"

# --- 3. 邮件发送系统 (修复 f-string 语法错误) ---
def send_mail(content_list):
    # 修复 image_b84199 提到的反斜杠错误，提前处理换行符
    full_body_html = "".join(content_list)
    
    if not full_body_html.strip():
        full_body_html = "<p style='color:orange;'>今日扫描完成，但目标源未发现足以生成摘要的文本信息。</p>"

    html_layout = f"""
    <div style="font-family:sans-serif;max-width:700px;margin:auto;border:1px solid #ddd;padding:30px;border-radius:15px;">
        <h2 style="color:#1a73e8;text-align:center;border-bottom:4px solid #1a73e8;padding-bottom:12px;">🌍 全球游戏动态·实测报告</h2>
        <div style="line-height:1.7;color:#333;">{full_body_html}</div>
        <div style="font-size:12px;color:#999;text-align:center;margin-top:40px;border-top:1px solid #eee;padding-top:20px;">
            情报来源：全球媒体 | 验证状态：解除时间限制 | 时间：{time.strftime("%Y-%m-%d %H:%M")}
        </div>
    </div>
    """
    msg = MIMEText(html_layout, 'html', 'utf-8')
    msg['From'] = f"SmartRadar <{SENDER_EMAIL}>"
    msg['To'] = RECIPIENT_EMAIL
    msg['Subject'] = Header(f"📊 全球游戏趋势探测 - {time.strftime('%m-%d')}", 'utf-8')
    
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASS)
            server.sendmail(SENDER_EMAIL, [RECIPIENT_EMAIL], msg.as_string())
        print("✅ 报告已送达")
    except Exception as e:
        print(f"❌ 邮件系统异常: {e}")

# --- 4. 主流程 ---
if __name__ == "__main__":
    results = []
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    
    for src in TARGET_SOURCES:
        try:
            print(f"正在扫描: {src['name']}...")
            r = requests.get(src['url'], headers=headers, timeout=25)
            # 强化抓取：去除脚本和样式标签，只留纯净文本
            soup = BeautifulSoup(r.text, 'html.parser')
            for element in soup(['script', 'style', 'nav', 'footer']):
                element.decompose()
            
            clean_text = soup.get_text(separator=' ', strip=True)
            summary = ai_summarize(clean_text)
            
            if "⚠️" not in summary and len(summary) > 50:
                # 修复 image_b84199 语法错误：不要在 f-string 内部用 replace('\n', '<br>')
                formatted_summary = summary.replace('\n', '<br>')
                section = f"""
                <div style="margin-bottom:25px;padding:20px;background:#fcfcfc;border-left:6px solid #1a73e8;">
                    <b style="color:#1a73e8;font-size:16px;">📍 来源：{src['name']}</b><br>
                    <div style="margin-top:12px;font-size:15px;">{formatted_summary}</div>
                </div>
                """
                results.append(section)
        except Exception as e:
            print(f"扫描跳过 {src['name']}: {e}")
            continue
        
    send_mail(results)
