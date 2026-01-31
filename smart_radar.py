import os
import time
import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.header import Header

# --- 1. 配置 ---
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
RECIPIENT_EMAIL = "tanweilin1987@gmail.com"
SENDER_EMAIL = os.environ.get('EMAIL_USER')
SENDER_PASS = os.environ.get('EMAIL_PASS')

# 扩展情报源：涵盖国内外深度媒体与数据平台
TARGET_SOURCES = [
    # 国内权威：专注买量与小游戏生态
    {"name": "GameLook", "url": "http://www.gamelook.com.cn/"},
    {"name": "手游那点事", "url": "https://nadianshi.com/"},
    
    # 海外一手：专注榜单变动与全球趋势
    {"name": "Pocket Gamer.biz", "url": "https://www.pocketgamer.biz/news/"},
    {"name": "MobileGamer.biz", "url": "https://mobilegamer.biz/"},
    {"name": "GameRefinery", "url": "https://www.gamerefinery.com/blog/"},
    
    # 行业大盘：全球投融资与宏观动态
    {"name": "GamesIndustry.biz", "url": "https://www.gamesindustry.biz/"},
    {"name": "VentureBeat (Games)", "url": "https://venturebeat.com/category/games/"}
]

# --- 2. AI 逻辑：纯净翻译模式 (绕过安全拦截) ---
def ai_summarize(content, source_name):
    if not GEMINI_API_KEY: return None
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    prompt = f"你是游戏行业资深编辑。请将以下来自 {source_name} 的动态翻译为中文摘要。若包含小游戏、买量或榜单内容请重点突出。每条一行，不要多余废话：\n{content}"
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ],
        "generationConfig": {"temperature": 0.1, "maxOutputTokens": 800}
    }
    
    try:
        response = requests.post(api_url, json=payload, timeout=30)
        res_json = response.json()
        if "candidates" in res_json and res_json["candidates"][0].get("content"):
            return res_json["candidates"][0]["content"]["parts"][0]["text"].strip()
    except:
        pass
    return None

# --- 3. 主程序：多源探测与备份输出 ---
def fetch_news(src):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        r = requests.get(src['url'], headers=headers, timeout=20)
        if r.status_code != 200: return None
        
        soup = BeautifulSoup(r.text, 'html.parser')
        # 优化抓取：过滤掉导航栏等干扰字符
        titles = [t.text.strip() for t in soup.find_all(['h2', 'h3'])[:12] if len(t.text.strip()) > 10]
        
        if titles:
            summary = ai_summarize("\n".join(titles), src['name'])
            # 解决 f-string 语法坑
            display = summary.replace('\n', '<br>') if summary else "AI响应异常，展示原始标题：<br>" + "<br>".join(titles)
            return "<h3>📍 " + src['name'] + "</h3><div style='background:#f9f9f9; padding:12px; border-radius:8px;'>" + display + "</div>"
    except:
        return None
    return None

if __name__ == "__main__":
    final_results = []
    for src in TARGET_SOURCES:
        print(f"📡 探测中: {src['name']}...")
        result = fetch_news(src)
        if result: final_results.append(result)

    # 邮件发送逻辑
    if final_results:
        html_body = f"""
        <div style="font-family:sans-serif; max-width:650px; margin:auto; border:1px solid #ddd; padding:20px; border-radius:12px;">
            <h2 style="color:#1a73e8; border-bottom:2px solid #1a73e8; padding-bottom:8px;">🛰️ 全球游戏·情报雷达 (多源版)</h2>
            {"".join(final_results)}
            <p style="font-size:11px; color:#aaa; text-align:center; margin-top:20px;">时间: {time.strftime("%Y-%m-%d %H:%M")}</p>
        </div>
        """
        msg = MIMEText(html_body, 'html', 'utf-8')
        msg['From'] = f"SmartRadar <{SENDER_EMAIL}>"
        msg['To'] = RECIPIENT_EMAIL
        msg['Subject'] = Header(f"🎮 市场深度简报(7源) - {time.strftime('%m-%d')}", 'utf-8')
        
        try:
            with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
                server.starttls()
                server.login(SENDER_EMAIL, SENDER_PASS)
                server.sendmail(SENDER_EMAIL, [RECIPIENT_EMAIL], msg.as_string())
            print("✅ 报告已送达")
        except Exception as e:
            print(f"❌ 发送失败: {e}")
