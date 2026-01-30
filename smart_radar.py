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

# --- 2. AI 核心引擎 (锁定 v1beta 兼容路径) ---
def ai_summarize(content):
    if not GEMINI_API_KEY: return "❌ 错误：未配置 Key"
    
    # 锁定 v1beta 路径，这是目前最稳定的免费层级端点
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    # 放宽 Prompt 限制，确保 AI 只要看到新闻就总结
    prompt = (
        "你是一位移动游戏分析师。请从提供的网页文本中提取 3 条最新的行业动态或趋势。"
        "必须使用中文回复。如果内容不完整，请基于片段提供最有价值的信息。"
        f"\n\n待分析内容：\n{content[:9000]}"
    )
    
    try:
        response = requests.post(api_url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=60)
        res_json = response.json()
        if "candidates" in res_json:
            return res_json["candidates"][0]["content"]["parts"][0]["text"]
        return "⚠️ AI 分析中未发现明确动态"
    except Exception as e:
        return f"⚠️ 接口请求失败: {str(e)}"

# --- 3. 邮件发送系统 (彻底修复 f-string 语法错误) ---
def send_mail(content_list):
    # 预先处理所有内容的换行符，避免在 f-string 内部进行处理
    processed_body = "".join(content_list)
    
    if not processed_body.strip():
        processed_body = "<p style='color:orange;'>今日扫描完成，目标网站结构可能已变更，导致文本提取为空。</p>"

    html_layout = f"""
    <div style="font-family:sans-serif;max-width:700px;margin:auto;border:1px solid #ddd;padding:30px;border-radius:15px;">
        <h2 style="color:#1a73e8;text-align:center;border-bottom:4px solid #1a73e8;padding-bottom:12px;">🌍 全球游戏动态·探测报告</h2>
        <div style="line-height:1.7;color:#333;">{processed_body}</div>
        <div style="font-size:12px;color:#999;text-align:center;margin-top:40px;border-top:1px solid #eee;padding-top:20px;">
            验证状态：深度文本清洗 | 引擎：Gemini 1.5 Flash | 时间：{time.strftime("%Y-%m-%d %H:%M")}
        </div>
    </div>
    """
    msg = MIMEText(html_layout, 'html', 'utf-8')
    msg['From'] = f"SmartRadar <{SENDER_EMAIL}>"
    msg['To'] = RECIPIENT_EMAIL
    msg['Subject'] = Header(f"📊 趋势雷达 - {time.strftime('%m-%d')}", 'utf-8')
    
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASS)
            server.sendmail(SENDER_EMAIL, [RECIPIENT_EMAIL], msg.as_string())
        print("✅ 报告已发送")
    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")

# --- 4. 主流程 (强化文本提取) ---
if __name__ == "__main__":
    results = []
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    for src in TARGET_SOURCES:
        try:
            print(f"正在探测: {src['name']}...")
            r = requests.get(src['url'], headers=headers, timeout=30)
            soup = BeautifulSoup(r.text, 'html.parser')
            
            # 强力清洗：剔除所有脚本、样式和页脚，直奔正文
            for element in soup(['script', 'style', 'nav', 'footer', 'header']):
                element.decompose()
            
            clean_text = soup.get_text(separator=' ', strip=True)
            summary = ai_summarize(clean_text)
            
            if "⚠️" not in summary and len(summary) > 30:
                # 修复 image_b84199 语法错误：提前转换 HTML 换行
                html_summary = summary.replace('\n', '<br>')
                section = f"""
                <div style="margin-bottom:25px;padding:20px;background:#f9f9f9;border-left:5px solid #1a73e8;">
                    <b style="color:#1a73e8;font-size:16px;">📍 来源：{src['name']}</b><br>
                    <div style="margin-top:10px;font-size:14px;">{html_summary}</div>
                </div>
                """
                results.append(section)
        except:
            continue
            
    send_mail(results)
