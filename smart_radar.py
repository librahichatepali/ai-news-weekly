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

TARGET_SOURCES = [
    {"name": "Pocket Gamer", "url": "https://www.pocketgamer.biz/feed/"},
    {"name": "MobileGamer", "url": "https://mobilegamer.biz/feed/"}
]

# --- 2. 翻译官 AI：取消所有屏蔽词 ---
def ai_summarize(content, source_name):
    if not GEMINI_API_KEY: return "AI Key Missing"
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    # 强制要求寻找小游戏内容，且必须凑足 4 条
    prompt = f"请翻译以下 {source_name} 的动态。重点关注'小游戏'、'排行榜'。强制列出4条中文摘要，严禁说没内容：\n{content}"
    
    try:
        response = requests.post(api_url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=60)
        res_json = response.json()
        return res_json["candidates"][0]["content"]["parts"][0]["text"].strip()
    except:
        return ""

# --- 3. 稳健邮件发送 ---
def send_mail(content_list, debug_info):
    main_body = "".join(content_list) if content_list else f"<p>调试信息：{debug_info}</p>"
    
    html_layout = f"""
    <div style="font-family:sans-serif; border:1px solid #eee; padding:20px;">
        <h2 style="color:#1a73e8;">🛰️ 情报抓取能力测试</h2>
        {main_body}
        <p style="font-size:12px; color:#aaa; margin-top:20px;">时间: {time.strftime("%Y-%m-%d %H:%M")}</p>
    </div>
    """
    
    msg = MIMEText(html_layout, 'html', 'utf-8')
    msg['From'] = f"SmartRadar <{SENDER_EMAIL}>"
    msg['To'] = RECIPIENT_EMAIL
    msg['Subject'] = Header(f"【测试】小游戏专题追踪 - {time.strftime('%m-%d')}", 'utf-8')
    
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASS)
            server.sendmail(SENDER_EMAIL, [RECIPIENT_EMAIL], msg.as_string())
        print("✅ 邮件已发送")
    except Exception as e:
        print(f"❌ 发送失败: {e}")

# --- 4. 主逻辑：避开 f-string 语法坑 ---
if __name__ == "__main__":
    final_results = []
    debug_log = ""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124'}

    for src in TARGET_SOURCES:
        try:
            print(f"📡 抓取: {src['name']}...")
            r = requests.get(src['url'], headers=headers, timeout=30)
            if r.status_code != 200:
                debug_log += f"[{src['name']} Code {r.status_code}] "
                continue
                
            soup = BeautifulSoup(r.text, 'xml')
            items = soup.find_all('item')[:8]
            titles = [it.find('title').text for it in items if it.find('title')]
            
            if titles:
                summary = ai_summarize("\n".join(titles), src['name'])
                if summary:
                    # 关键修复：不在 f-string 内部做 replace，彻底解决 SyntaxError
                    formatted_summary = summary.replace('\n', '<br>')
                    section = "<h3>📍 " + src['name'] + "</h3><p>" + formatted_summary + "</p>"
                    final_results.append(section)
            else:
                debug_log += f"[{src['name']} 解析为空] "
        except Exception as e:
            debug_log += f"[{src['name']} 报错: {str(e)[:30]}] "
            
    send_mail(final_results, debug_log if debug_log else "未发现抓取异常")
