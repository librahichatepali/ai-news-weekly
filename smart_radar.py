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

# 更新了更稳健的 RSS 链接，解决 404 问题
TARGET_SOURCES = [
    {"name": "PocketGamer.biz", "url": "https://www.pocketgamer.biz/feed/"},
    {"name": "GameIndustry.biz", "url": "https://www.gamesindustry.biz/rss/articles"}
]

# --- 2. 翻译官 AI：锁定小游戏 + 强制输出 ---
def ai_summarize(content, source_name):
    if not GEMINI_API_KEY: return "AI Key Missing"
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    # 强制要求寻找小游戏内容，严禁说“无深度”
    prompt = f"""
    任务：请翻译以下来自 {source_name} 的动态。
    要求：
    1. 重点提取与'小游戏(Mini-games)'、'排行榜(Charts)'、'新游上线'相关的内容。
    2. 必须输出至少 4 条中文摘要，严禁说没内容。
    
    待翻译内容：
    {content}
    """
    
    try:
        response = requests.post(api_url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=60)
        res_json = response.json()
        return res_json["candidates"][0]["content"]["parts"][0]["text"].strip()
    except:
        return ""

# --- 3. 稳健邮件发送 ---
def send_mail(content_list, debug_info):
    main_body = "".join(content_list) if content_list else f"<p style='color:red;'>⚠️ 调试警报：{debug_info}</p>"
    
    html_layout = f"""
    <div style="font-family:sans-serif; border:1px solid #eee; padding:20px; max-width:600px; margin:auto;">
        <h2 style="color:#1a73e8; border-bottom:2px solid #1a73e8; padding-bottom:10px;">🎮 全球游戏·情报雷达</h2>
        {main_body}
        <p style="font-size:11px; color:#aaa; margin-top:20px; text-align:center; border-top:1px solid #eee; padding-top:10px;">
            模式: 强制4条+小游戏追踪 | 时间: {time.strftime("%Y-%m-%d %H:%M")}
        </p>
    </div>
    """
    
    msg = MIMEText(html_layout, 'html', 'utf-8')
    msg['From'] = f"SmartRadar <{SENDER_EMAIL}>"
    msg['To'] = RECIPIENT_EMAIL
    msg['Subject'] = Header(f"🎮 市场动态简报 - {time.strftime('%m-%d')}", 'utf-8')
    
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASS)
            server.sendmail(SENDER_EMAIL, [RECIPIENT_EMAIL], msg.as_string())
        print("✅ 邮件已成功送达")
    except Exception as e:
        print(f"❌ 发送失败: {e}")

# --- 4. 主运行程序：彻底修复语法坑 ---
if __name__ == "__main__":
    final_results = []
    debug_log = ""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/110.0.0.0'}

    for src in TARGET_SOURCES:
        try:
            print(f"📡 抓取中: {src['name']}...")
            r = requests.get(src['url'], headers=headers, timeout=20)
            if r.status_code != 200:
                debug_log += f"[{src['name']} Code {r.status_code}] "
                continue
            
            # 使用 'html.parser' 替代 'xml' 以提高在 GitHub Actions 环境下的兼容性
            soup = BeautifulSoup(r.text, 'html.parser')
            items = soup.find_all('item')[:8]
            titles = [it.find('title').text for it in items if it.find('title')]
            
            if titles:
                summary = ai_summarize("\n".join(titles), src['name'])
                if summary:
                    # 关键：将 replace 操作移出 f-string 内部，彻底解决 SyntaxError
                    clean_summary = summary.replace('\n', '<br>')
                    section = f"<h3>📍 {src['name']}</h3><div style='font-size:14px;'>{clean_summary}</div>"
                    final_results.append(section)
            else:
                debug_log += f"[{src['name']} 未解析到标题] "
        except Exception as e:
            debug_log += f"[{src['name']} 报错: {str(e)[:30]}] "

    send_mail(final_results, debug_log if debug_log else "内容获取正常")
