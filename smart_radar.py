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
    {"name": "MobileGamer.biz (行业动态)", "url": "https://mobilegamer.biz/feed/"},
    {"name": "GameRefinery (市场趋势)", "url": "https://www.gamerefinery.com/feed/"}
]

# --- 2. AI 核心：强制产出逻辑 ---
def ai_summarize(content, source_name):
    if not GEMINI_API_KEY: return ""
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    # 强制 AI 翻译所有标题，禁止其拒绝回答
    prompt = f"""
    任务：你是一个专业游戏翻译。请将来自 {source_name} 的新闻标题翻译成中文。
    要求：
    1. 简洁直接，按序号排列翻译后的标题。
    2. 哪怕新闻很简短，也要列出翻译结果。
    3. 不得回复“无重大更新”或“暂无新内容”。
    
    待处理列表：
    {content}
    """
    
    try:
        response = requests.post(api_url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=60)
        res_json = response.json()
        if "candidates" in res_json:
            return res_json["candidates"][0]["content"]["parts"][0]["text"].strip()
        return ""
    except:
        return ""

# --- 3. 邮件系统：加固物理保底机制 ---
def send_mail(content_list, backup_titles):
    ai_output = "".join(content_list).strip()
    
    # 保底机制：如果 AI 没说话，强制显示原始英文标题
    if not ai_output:
        backup_html = "<ul>" + "".join([f"<li>{t}</li>" for t in backup_titles]) + "</ul>"
        main_body = f"""
        <div style="padding:15px; background:#fff3cd; color:#856404; border-radius:8px; border:1px solid #ffeeba;">
            ⚠️ AI 判定今日无深度资讯，以下为系统直接抓取的原始标题列表：<br>{backup_html}
        </div>
        """
    else:
        main_body = ai_output

    current_time = time.strftime("%Y-%m-%d %H:%M")
    html_layout = f"""
    <div style="font-family:sans-serif; max-width:650px; margin:auto; border:1px solid #eee; padding:25px; border-radius:15px; background:#fff;">
        <h2 style="color:#1a73e8; text-align:center; border-bottom:2px solid #1a73e8; padding-bottom:10px;">🎮 全球游戏·动态雷达</h2>
        <div style="line-height:1.8; color:#333;">{main_body}</div>
        <div style="font-size:12px; color:#aaa; text-align:center; margin-top:30px; border-top:1px solid #f0f0f0; padding-top:15px;">
            引擎: Gemini 1.5 Flash | 模式: 强力产出 | 时间: {current_time}
        </div>
    </div>
    """
    
    msg = MIMEText(html_layout, 'html', 'utf-8')
    msg['From'] = f"SmartRadar <{SENDER_EMAIL}>"
    msg['To'] = RECIPIENT_EMAIL
    msg['Subject'] = Header(f"📊 探测报告 - {time.strftime('%m-%d')}", 'utf-8')
    
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASS)
            server.sendmail(SENDER_EMAIL, [RECIPIENT_EMAIL], msg.as_string())
        print("✅ 邮件已成功发出")
    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")

# --- 4. 运行逻辑：彻底规避语法崩溃 ---
if __name__ == "__main__":
    final_results = []
    all_captured_titles = []
    
    for src in TARGET_SOURCES:
        try:
            print(f"📡 正在扫描: {src['name']}")
            r = requests.get(src['url'], timeout=20)
            soup = BeautifulSoup(r.text, 'xml')
            items = soup.find_all('item')[:6] 
            
            feed_text = ""
            for it in items:
                title = it.find('title').text
                all_captured_titles.append(f"[{src['name']}] {title}")
                feed_text += f"- {title}\n"
            
            if feed_text:
                summary = ai_summarize(feed_text, src['name'])
                if summary:
                    # 将换行符提前处理，规避 f-string 中的反斜杠错误
                    safe_summary = summary.replace('\n', '<br>')
                    section = f"""
                    <div style="margin-bottom:20px; padding:15px; background:#f8f9fa; border-left:5px solid #1a73e8;">
                        <b style="color:#1a73e8;">📍 {src['name']}</b><br>
                        <div style="margin-top:8px;">{safe_summary}</div>
                    </div>
                    """
                    final_results.append(section)
        except Exception as e:
            print(f"⚠️ {src['name']} 异常: {e}")
            
    send_mail(final_results, all_captured_titles)
