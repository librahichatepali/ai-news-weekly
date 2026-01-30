import os
import time
import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.header import Header

# --- 1. 环境配置 ---
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
RECIPIENT_EMAIL = "tanweilin1987@gmail.com"
SENDER_EMAIL = os.environ.get('EMAIL_USER')
SENDER_PASS = os.environ.get('EMAIL_PASS')

TARGET_SOURCES = [
    {"name": "Pocket Gamer", "url": "https://www.pocketgamer.biz/feed/"},
    {"name": "MobileGamer.biz", "url": "https://mobilegamer.biz/feed/"},
    {"name": "GameRefinery", "url": "https://www.gamerefinery.com/feed/"}
]

# --- 2. 核心：强制 AI 翻译 ---
def ai_summarize(content, source_name):
    if not GEMINI_API_KEY: return ""
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    # 修改 Prompt：严禁判定“无价值”，强制要求产出中文翻译列表
    prompt = f"""
    任务：你是一个专业游戏新闻官。请将来自 {source_name} 的新闻标题翻译成精炼的中文。
    要求：
    1. 必须翻译，不得跳过，哪怕是简短的更新。
    2. 禁止回答“今日无深度资讯”或“无重要更新”。
    3. 输出格式：序号. [中文标题]
    
    待处理内容：
    {content}
    """
    
    try:
        response = requests.post(api_url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=60)
        res_json = response.json()
        if "candidates" in res_json:
            return res_json["candidates"][0]["content"]["parts"][0]["text"].strip()
        return ""
    except Exception:
        return ""

# --- 3. 邮件发送：修复变量名报错 ---
def send_mail(content_list, backup_titles):
    ai_output = "".join(content_list).strip()
    
    # 彻底修复 image_9ab91c 中的 NameError 变量名
    if not ai_output:
        # 确保使用正确的变量名 backup_titles
        list_items = "".join([f"<li>{t}</li>" for t in backup_titles])
        main_body = f"""
        <div style="padding:15px; background:#fff3cd; color:#856404; border-radius:8px; border:1px solid #ffeeba;">
            ⚠️ 系统侦测到抓取内容，但 AI 处理异常。以下为原始标题列表：<br>
            <ul>{list_items}</ul>
        </div>
        """
    else:
        main_body = ai_output

    html_layout = f"""
    <div style="font-family:sans-serif; max-width:650px; margin:auto; border:1px solid #eee; padding:25px; border-radius:15px; background:#fff;">
        <h2 style="color:#1a73e8; text-align:center; border-bottom:2px solid #1a73e8; padding-bottom:10px;">📊 全球游戏·雷达报告</h2>
        <div style="line-height:1.8; color:#333;">{main_body}</div>
        <div style="font-size:11px; color:#aaa; text-align:center; margin-top:30px; border-top:1px solid #f0f0f0; padding-top:15px;">
            引擎: Gemini 1.5 Flash | 模式: 强力播报 | 时间: {time.strftime("%Y-%m-%d %H:%M")}
        </div>
    </div>
    """
    
    msg = MIMEText(html_layout, 'html', 'utf-8')
    msg['From'] = f"SmartRadar <{SENDER_EMAIL}>"
    msg['To'] = RECIPIENT_EMAIL
    msg['Subject'] = Header(f"🎮 趋势探测报告 - {time.strftime('%m-%d')}", 'utf-8')
    
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASS)
            server.sendmail(SENDER_EMAIL, [RECIPIENT_EMAIL], msg.as_string())
        print("✅ 报告已成功发出")
    except Exception as e:
        print(f"❌ 发送失败: {e}")

# --- 4. 主程序：修正变量流 ---
if __name__ == "__main__":
    final_results = []
    all_captured_titles = [] # 修正变量名
    
    for src in TARGET_SOURCES:
        try:
            print(f"📡 抓取中: {src['name']}...")
            r = requests.get(src['url'], timeout=20)
            soup = BeautifulSoup(r.text, 'xml')
            items = soup.find_all('item')[:5] 
            
            raw_text = ""
            for it in items:
                title = it.find('title').text
                all_captured_titles.append(f"[{src['name']}] {title}")
                raw_text += f"- {title}\n"
            
            if raw_text:
                summary = ai_summarize(raw_text, src['name'])
                if summary:
                    # 转换换行符确保 HTML 显示
                    safe_summary = summary.replace('\n', '<br>')
                    section = f"""
                    <div style="margin-bottom:20px; padding:15px; background:#f8f9fa; border-left:5px solid #1a73e8;">
                        <b style="color:#1a73e8;">📍 {src['name']}</b><br>
                        <div style="margin-top:8px; font-size:14px;">{safe_summary}</div>
                    </div>
                    """
                    final_results.append(section)
        except Exception as e:
            print(f"⚠️ {src['name']} 异常: {e}")
            
    send_mail(final_results, all_captured_titles)
