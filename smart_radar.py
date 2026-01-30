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

# 监控外网源：抓取成功率极高，且是小游戏创新的源头
TARGET_SOURCES = [
    {"name": "Pocket Gamer News", "url": "https://www.pocketgamer.biz/news/"},
    {"name": "GameRefinery Blog", "url": "https://www.gamerefinery.com/blog/"},
    {"name": "MobileGamer News", "url": "https://mobilegamer.biz/news/"}
]

# --- 2. AI 引擎 (多路径兼容 + 宽松筛选) ---
def ai_summarize(content):
    if not GEMINI_API_KEY: return "❌ 错误：未配置 API KEY"
    
    # 定义尝试的 API 路径列表，解决 models/not found 报错
    base_urls = [
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent",
        "https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent"
    ]
    
    # 宽松的 Prompt：不再死磕“2026年1月”，而是抓取“最新干货”
    prompt = (
        "你是一位资深游戏猎头。请从下文中提炼【最新】的移动游戏、超休闲游戏或小游戏行业动态。"
        "不要局限于特定日期，请提取网页中显示的最有价值的 3 条情报。"
        "要求：必须使用中文（简体）回复。内容如下：\n\n"
        f"{content[:8000]}" # 扩大抓取量，确保覆盖到正文
    )

    for url in base_urls:
        try:
            full_url = f"{url}?key={GEMINI_API_KEY}"
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            response = requests.post(full_url, json=payload, timeout=45)
            res_json = response.json()
            
            if "candidates" in res_json:
                return res_json["candidates"][0]["content"]["parts"][0]["text"]
            continue # 如果当前路径报错，尝试下一个
        except: continue
        
    return "⚠️ AI 分析通道暂不可用，请检查 API 配额或网络。"

# --- 3. 邮件发送系统 ---
def send_mail(content_list):
    full_body = "".join(content_list)
    if not full_body.strip():
        full_body = "<p style='color:orange;'>今日已完成扫描，但未发现足够长度的动态摘要，请检查目标源结构。</p>"

    html_layout = f"""
    <div style="font-family:sans-serif;max-width:700px;margin:auto;border:1px solid #eee;padding:25px;border-radius:12px;">
        <h2 style="color:#1a73e8;text-align:center;border-bottom:3px solid #1a73e8;padding-bottom:12px;">🛡️ 全球游戏动态·实测报告</h2>
        <div style="line-height:1.8;">{full_body}</div>
        <div style="font-size:11px;color:#999;text-align:center;margin-top:30px;border-top:1px solid #f0f0f0;padding-top:15px;">
            情报来源：PocketGamer / GameRefinery / MobileGamer | 状态：宽松筛选模式 | 时间：{time.strftime("%Y-%m-%d %H:%M")}
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
        print("✅ 报告已成功发出")
    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")

# --- 4. 自动化主流程 ---
if __name__ == "__main__":
    results = []
    # 模拟真实浏览器请求
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    
    for src in TARGET_SOURCES:
        try:
            print(f"正在分析: {src['name']}...")
            r = requests.get(src['url'], headers=headers, timeout=25)
            # 使用 BeautifulSoup 提取所有文本，交由 AI 过滤干扰项
            soup = BeautifulSoup(r.text, 'html.parser')
            page_text = soup.get_text(separator=' ', strip=True)
            
            summary = ai_summarize(page_text)
            
            if "⚠️" not in summary and len(summary) > 30:
                safe_summary = summary.replace('\n', '<br>')
                section = f"""
                <div style="margin-bottom:20px;padding:15px;background:#f9f9f9;border-left:5px solid #1a73e8;">
                    <b style="color:#1a73e8;">📍 来源：{src['name']}</b><br>
                    <div style="margin-top:10px;font-size:14px;color:#333;">{safe_summary}</div>
                </div>
                """
                results.append(section)
        except Exception as e:
            print(f"跳过 {src['name']}：{e}")
            continue
        
    send_mail(results)
