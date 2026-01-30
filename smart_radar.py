import os
import time
import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.header import Header

# --- 1. 基础配置 ---
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
RECIPIENT_EMAIL = "tanweilin1987@gmail.com"
SENDER_EMAIL = os.environ.get('EMAIL_USER')
SENDER_PASS = os.environ.get('EMAIL_PASS')

# 选择最不容易崩的源，直接抓取新闻列表页
TARGET_SOURCES = [
    {"name": "GameLook", "url": "http://www.gamelook.com.cn/"},
    {"name": "PocketGamer", "url": "https://www.pocketgamer.biz/"}
]

# --- 2. 强制翻译官 AI ---
def ai_summarize(content, source_name):
    if not GEMINI_API_KEY: return "API Key Missing"
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    # 解除所有安全限制，强制要求翻译 4 条
    payload = {
        "contents": [{"parts": [{"text": f"任务：翻译以下标题为中文，强制列出4条。严禁说无内容。\n内容：{content}"}]}],
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"}
        ]
    }
    
    try:
        response = requests.post(api_url, json=payload, timeout=40)
        res_json = response.json()
        # 稳健提取，防止 'candidates' 报错
        if "candidates" in res_json and res_json["candidates"][0].get("content"):
            return res_json["candidates"][0]["content"]["parts"][0]["text"].strip()
        return "AI 未返回内容"
    except Exception as e:
        return f"AI 异常: {str(e)[:20]}"

# --- 3. 稳健邮件发送 ---
def send_mail(content_list, debug_info):
    main_body = "".join(content_list) if content_list else f"<p>调试日志: {debug_info}</p>"
    
    html_layout = f"""
    <div style="font-family:sans-serif; border:1px solid #eee; padding:20px;">
        <h2 style="color:#1a73e8;">🛰️ 情报获取能力测试</h2>
        {main_body}
        <div style="font-size:11px; color:#aaa; margin-top:20px;">时间: {time.strftime("%Y-%m-%d %H:%M")}</div>
    </div>
    """
    
    msg = MIMEText(html_layout, 'html', 'utf-8')
    msg['From'] = f"SmartRadar <{SENDER_EMAIL}>"
    msg['To'] = RECIPIENT_EMAIL
    msg['Subject'] = Header(f"【压力测试】获取小游戏信息 - {time.strftime('%m-%d')}", 'utf-8')
    
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASS)
            server.sendmail(SENDER_EMAIL, [RECIPIENT_EMAIL], msg.as_string())
        print("✅ 邮件已发出")
    except Exception as e:
        print(f"❌ 发送失败: {e}")

# --- 4. 主逻辑：避开所有语法报错 ---
if __name__ == "__main__":
    final_results = []
    debug_log = ""
    # 模拟浏览器身份，防止被屏蔽
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/110.0.0.0'}

    for src in TARGET_SOURCES:
        try:
            print(f"📡 抓取: {src['name']}...")
            r = requests.get(src['url'], headers=headers, timeout=30)
            if r.status_code != 200:
                debug_log += f"[{src['name']} Code {r.status_code}] "
                continue
            
            # 使用最稳健的解析器，解决缺失构造器的报错
            soup = BeautifulSoup(r.text, 'html.parser')
            # 直接抓取所有 h2/h3 标题文字
            titles = [t.text.strip() for t in soup.find_all(['h2', 'h3'])[:15]]
            
            if titles:
                summary = ai_summarize("\n".join(titles), src['name'])
                if summary:
                    # 彻底解决 f-string 内部反斜杠报错
                    fmt_sum = summary.replace('\n', '<br>')
                    final_results.append("<h3>📍 " + src['name'] + "</h3><p>" + fmt_sum + "</p>")
            else:
                debug_log += f"[{src['name']} 未解析到标题] "
        except Exception as e:
            debug_log += f"[{src['name']} 报错: {str(e)[:20]}] "

    send_mail(final_results, debug_log if debug_log else "一切正常")
