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

# 切换为最稳定的 RSS 聚合源，避开 404
TARGET_SOURCES = [
    {"name": "GameRefinery", "url": "https://www.gamerefinery.com/feed/"},
    {"name": "PocketGamer.biz", "url": "https://www.pocketgamer.biz/feed/"},
    {"name": "MobileGamer.biz", "url": "https://mobilegamer.biz/feed/"}
]

# --- 2. 核心 AI 逻辑：关闭过滤，修复 'candidates' 报错 ---
def ai_summarize(content, source_name):
    if not GEMINI_API_KEY: return "Error: No API Key"
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    # 构造请求体，加入安全设置，防止 AI 拒绝回答
    payload = {
        "contents": [{"parts": [{"text": f"请翻译并摘要以下关于 {source_name} 的动态，重点关注小游戏和榜单，必须列出4条中文：\n{content}"}]}],
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]
    }
    
    try:
        response = requests.post(api_url, json=payload, timeout=60)
        res_json = response.json()
        
        # 稳健提取：检查是否有错误信息或被屏蔽
        if "candidates" in res_json and res_json["candidates"][0].get("content"):
            return res_json["candidates"][0]["content"]["parts"][0]["text"].strip()
        elif "error" in res_json:
            return f"API 报错: {res_json['error']['message']}"
        return "AI 判定内容敏感或无结果，已跳过。"
    except Exception as e:
        return f"请求异常: {str(e)[:30]}"

# --- 3. 邮件发送：避开 f-string 反斜杠语法陷阱 ---
def send_mail(content_list, debug_info):
    main_body = "".join(content_list)
    if not main_body:
        main_body = f"<p style='color:orange;'>诊断信息: {debug_info}</p>"
        
    html_layout = f"""
    <div style="font-family:sans-serif; max-width:600px; margin:auto; border:1px solid #eee; padding:20px; border-radius:10px;">
        <h2 style="color:#1a73e8; border-bottom:2px solid #1a73e8; padding-bottom:10px;">🚀 情报雷达·深度探测版</h2>
        {main_body}
        <div style="font-size:12px; color:#aaa; margin-top:20px; text-align:center;">
            状态: 安全过滤已解除 | 时间: {time.strftime("%Y-%m-%d %H:%M")}
        </div>
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
        print("✅ 邮件已成功发送")
    except Exception as e:
        print(f"❌ 发送失败: {e}")

# --- 4. 主流程 ---
if __name__ == "__main__":
    final_results = []
    debug_log = ""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/110.0.0.0'}

    for src in TARGET_SOURCES:
        try:
            print(f"📡 探测中: {src['name']}...")
            r = requests.get(src['url'], headers=headers, timeout=30)
            if r.status_code != 200:
                debug_log += f"[{src['name']} {r.status_code}] "
                continue
            
            soup = BeautifulSoup(r.text, 'xml')
            items = soup.find_all('item')[:10]
            titles = [it.find('title').text for it in items if it.find('title')]
            
            if titles:
                summary = ai_summarize("\n".join(titles), src['name'])
                if summary:
                    # 关键修复：将 replace 移出 f-string
                    clean_summary = summary.replace('\n', '<br>')
                    section = "<h3>📍 " + src['name'] + "</h3><p>" + clean_summary + "</p>"
                    final_results.append(section)
            else:
                debug_log += f"[{src['name']} 无标题] "
        except Exception as e:
            debug_log += f"[{src['name']} 报错: {str(e)[:20]}] "

    send_mail(final_results, debug_log if debug_log else "探测完毕")
