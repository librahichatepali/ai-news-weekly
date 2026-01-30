import os
import time
import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.header import Header

# --- 1. 核心配置 ---
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
RECIPIENT_EMAIL = "tanweilin1987@gmail.com"
SENDER_EMAIL = os.environ.get('EMAIL_USER')
SENDER_PASS = os.environ.get('EMAIL_PASS')

# 保持当前运行最稳的源
TARGET_SOURCES = [
    {"name": "GameLook", "url": "http://www.gamelook.com.cn/"},
    {"name": "Pocket Gamer", "url": "https://www.pocketgamer.biz/"}
]

# --- 2. 升级版 AI 逻辑：纯粹翻译模式 ---
def ai_summarize(content, source_name):
    if not GEMINI_API_KEY: return None
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    # 采用更中性的 Prompt，减少 AI 判定的“主观风险”
    prompt = f"请将以下{source_name}的新闻标题翻译成简洁的中文摘要，每条一行：\n{content}"
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
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

# --- 3. 稳健邮件发送 ---
def send_mail(sections, debug_log):
    # 优先展示翻译内容，若 AI 失败则自动切换为原始标题备份
    content = "".join(sections) if sections else f"<p>调试信息: {debug_log}</p>"
    
    html_layout = f"""
    <div style="font-family:sans-serif; padding:20px; border:1px solid #ddd; border-radius:10px;">
        <h2 style="color:#1a73e8; border-bottom:2px solid #1a73e8; padding-bottom:8px;">📊 每日情报·小游戏雷达</h2>
        {content}
        <hr style="border:0; border-top:1px solid #eee; margin-top:20px;">
        <p style="font-size:11px; color:#aaa; text-align:center;">状态: AI+原始备份模式 | 时间: {time.strftime("%Y-%m-%d %H:%M")}</p>
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
        print("✅ 报告已送达")
    except Exception as e:
        print(f"❌ 邮件发送异常: {e}")

# --- 4. 主逻辑 ---
if __name__ == "__main__":
    final_sections = []
    log_info = ""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

    for src in TARGET_SOURCES:
        try:
            r = requests.get(src['url'], headers=headers, timeout=20)
            if r.status_code != 200: continue
            
            soup = BeautifulSoup(r.text, 'html.parser')
            # 抓取逻辑增强：仅抓取有实质内容的标题
            titles = [t.text.strip() for t in soup.find_all(['h2', 'h3'])[:12] if len(t.text.strip()) > 8]
            
            if titles:
                summary = ai_summarize("\n".join(titles), src['name'])
                
                # 若翻译成功则格式化，否则展示原始列表并标注
                if summary:
                    body_text = summary.replace('\n', '<br>')
                else:
                    body_text = "<span style='color:#e67e22;'>AI 响应超时，展示原始列表：</span><br>" + "<br>".join(titles)
                
                # 修复 f-string 语法问题
                section_html = "<h3>📍 " + src['name'] + "</h3><div style='line-height:1.6; color:#444;'>" + body_text + "</div>"
                final_sections.append(section_html)
        except Exception as e:
            log_info += f"[{src['name']} 错误] "

    send_mail(final_sections, log_info)
