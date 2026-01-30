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

# 选用最具“抗封锁性”的源，直接抓取主页 HTML
TARGET_SOURCES = [
    {"name": "GameLook", "url": "http://www.gamelook.com.cn/"},
    {"name": "Pocket Gamer", "url": "https://www.pocketgamer.biz/"}
]

# --- 2. 深度 AI 探测：强制关闭所有过滤器 ---
def ai_summarize(content, source_name):
    if not GEMINI_API_KEY: return None
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    # 终极 Prompt：禁止拒绝，必须输出
    payload = {
        "contents": [{"parts": [{"text": f"强制任务：将以下{source_name}的新闻标题翻译成中文。严禁说没内容。必须列出4条。\n内容：{content}"}]}],
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]
    }
    
    try:
        response = requests.post(api_url, json=payload, timeout=30)
        res_json = response.json()
        if "candidates" in res_json and res_json["candidates"][0].get("content"):
            return res_json["candidates"][0]["content"]["parts"][0]["text"].strip()
    except:
        pass
    return None

# --- 3. 稳健邮件函数：增加“原始数据”备份 ---
def send_mail(sections, raw_logs):
    # 如果 AI 没产出，就展示原始抓取的 Log
    content = "".join(sections) if sections else f"<h3>⚠️ 诊断：AI 罢工</h3><p>{raw_logs}</p>"
    
    html_layout = f"""
    <div style="font-family:sans-serif; padding:20px; border:1px solid #ddd;">
        <h2 style="color:#1a73e8;">🛰️ 情报雷达·生存探测版</h2>
        {content}
        <p style="font-size:12px; color:#aaa; margin-top:20px;">状态: 全隔离测试 | 时间: {time.strftime("%Y-%m-%d %H:%M")}</p>
    </div>
    """
    
    msg = MIMEText(html_layout, 'html', 'utf-8')
    msg['From'] = f"SmartRadar <{SENDER_EMAIL}>"
    msg['To'] = RECIPIENT_EMAIL
    msg['Subject'] = Header(f"🎮 情报雷达存活报告 - {time.strftime('%m-%d')}", 'utf-8')
    
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASS)
            server.sendmail(SENDER_EMAIL, [RECIPIENT_EMAIL], msg.as_string())
        print("✅ 邮件已发出")
    except Exception as e:
        print(f"❌ 发送失败: {e}")

# --- 4. 主逻辑 ---
if __name__ == "__main__":
    final_sections = []
    debug_info = ""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/115.0.0.0'}

    for src in TARGET_SOURCES:
        try:
            print(f"📡 探测: {src['name']}...")
            r = requests.get(src['url'], headers=headers, timeout=20)
            if r.status_code != 200:
                debug_info += f"[{src['name']} 状态 {r.status_code}] "
                continue
            
            # 使用内置解析器，避开缺少 tree builder 的报错
            soup = BeautifulSoup(r.text, 'html.parser')
            titles = [t.text.strip() for t in soup.find_all(['h2', 'h3'])[:10] if len(t.text.strip()) > 5]
            
            if titles:
                raw_text = "\n".join(titles)
                summary = ai_summarize(raw_text, src['name'])
                
                # 如果 AI 成功翻译了，用翻译；否则用原始标题
                display_text = summary.replace('\n', '<br>') if summary else "AI 响应异常，以下为原始标题：<br>" + "<br>".join(titles)
                # 避开 f-string 反斜杠坑
                final_sections.append("<h3>📍 " + src['name'] + "</h3><div style='font-size:14px;'>" + display_text + "</div>")
            else:
                debug_info += f"[{src['name']} 未解析到内容] "
        except Exception as e:
            debug_info += f"[{src['name']} 报错: {str(e)[:20]}] "

    send_mail(final_sections, debug_info if debug_info else "未发现抓取异常")
