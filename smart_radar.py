import os
import time
import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.header import Header

# --- 1. 配置区域 ---
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
RECIPIENT_EMAIL = "tanweilin1987@gmail.com"
SENDER_EMAIL = os.environ.get('EMAIL_USER')
SENDER_PASS = os.environ.get('EMAIL_PASS')

TARGET_SOURCES = [
    {"name": "Pocket Gamer (移动游戏)", "url": "https://www.pocketgamer.biz/feed/"},
    {"name": "MobileGamer.biz (深度趋势)", "url": "https://mobilegamer.biz/feed/"},
    {"name": "GameRefinery (市场动态)", "url": "https://www.gamerefinery.com/feed/"}
]

# --- 2. AI 核心：不再判定，直接执行 ---
def ai_summarize(content, source_name):
    if not GEMINI_API_KEY: return "❌ Key未配置"
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    prompt = f"""
    作为专业的游戏行业助手，请将来自 {source_name} 的最新新闻标题翻译成中文。
    要求：
    1. 选出最相关的 3-5 条。
    2. 用简洁的中文说明它们是什么。
    3. 不得回复“无更新”，哪怕只是简单的标题列表。
    
    新闻列表：
    {content[:15000]}
    """
    
    try:
        response = requests.post(api_url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=60)
        res_json = response.json()
        if "candidates" in res_json:
            return res_json["candidates"][0]["content"]["parts"][0]["text"]
        return "⚠️ AI 未能生成摘要"
    except:
        return "⚠️ AI 连接超时"

# --- 3. 邮件发送系统：修复语法并增加保底 ---
def send_mail(content_list, backup_titles):
    combined_body = "".join(content_list)
    
    # 物理保底：如果 AI 没吐内容，直接展示原始抓取到的标题
    if not combined_body.strip():
        backup_str = "<br>".join(backup_titles)
        combined_body = f"""
        <div style="color:#d93025; background:#fce8e6; padding:15px; border-radius:8px;">
            <b>💡 AI 摘要失败，以下为今日原始抓取标题：</b><br>{backup_str}
        </div>
        """

    # 语法修复：大括号内严禁反斜杠
    current_time = time.strftime("%Y-%m-%d %H:%M")
    html_layout = f"""
    <div style="font-family:sans-serif; max-width:650px; margin:auto; border:1px solid #ddd; padding:25px; border-radius:15px;">
        <h2 style="color:#1a73e8; text-align:center;">📡 全球游戏情报汇总</h2>
        <div style="line-height:1.7;">{combined_body}</div>
        <hr style="border:0; border-top:1px solid #eee; margin:30px 0;">
        <div style="font-size:12px; color:#999; text-align:center;">
            模式：强制产出 | 时间：{current_time}
        </div>
    </div>
    """
    
    msg = MIMEText(html_layout, 'html', 'utf-8')
    msg['From'] = f"SmartRadar <{SENDER_EMAIL}>"
    msg['To'] = RECIPIENT_EMAIL
    msg['Subject'] = Header(f"📊 游戏探测报 - {time.strftime('%m-%d')}", 'utf-8')
    
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASS)
            server.sendmail(SENDER_EMAIL, [RECIPIENT_EMAIL], msg.as_string())
        print("✅ 发送成功")
    except Exception as e:
        print(f"❌ 发送失败: {e}")

# --- 4. 运行逻辑 ---
if __name__ == "__main__":
    results = []
    all_titles = [] # 用于保底展示
    
    for src in TARGET_SOURCES:
        try:
            r = requests.get(src['url'], timeout=20)
            soup = BeautifulSoup(r.text, 'xml')
            items = soup.find_all('item')[:10]
            
            source_content = ""
            for it in items:
                title = it.find('title').text if it.find('title') else ""
                all_titles.append(f"[{src['name']}] {title}")
                source_content += f"- {title}\n"
            
            if source_content:
                summary = ai_summarize(source_content, src['name'])
                # 在大括号外处理换行符，规避 SyntaxError
                safe_summary = summary.replace('\n', '<br>')
                section = f"""
                <div style="margin-bottom:20px; padding:15px; background:#f9f9f9; border-left:5px solid #1a73e8;">
                    <b>📍 {src['name']}</b><br>{safe_summary}
                </div>
                """
                results.append(section)
        except Exception as e:
            print(f"源 {src['name']} 异常: {e}")
            
    send_mail(results, all_titles)
