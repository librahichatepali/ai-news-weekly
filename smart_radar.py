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

# 更换为极其稳定的源（这些源几乎不会返回 404）
TARGET_SOURCES = [
    {"name": "GameLook (移动游戏专栏)", "url": "https://www.gamelook.com.cn/category/mobile-game"},
    {"name": "PocketGamer News", "url": "https://www.pocketgamer.com/news/"}
]

# --- 2. 核心 AI 逻辑：强制翻译，忽略屏蔽词 ---
def ai_summarize(content, source_name):
    if not GEMINI_API_KEY: return "AI Key Missing"
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    # 强制 AI 聚焦“小游戏/排行榜”，并锁定 4 条输出
    prompt = f"""
    请翻译以下来自 {source_name} 的新闻。
    要求：
    1. 重点提取关于'小游戏'、'热销榜'、'H5游戏'的信息。
    2. 禁止说无深度或无内容，必须列出 4 条简短中文摘要。
    
    内容如下：
    {content}
    """
    
    try:
        response = requests.post(api_url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=60)
        res_json = response.json()
        return res_json["candidates"][0]["content"]["parts"][0]["text"].strip()
    except:
        return ""

# --- 3. 发送邮件逻辑：修复语法报错 ---
def send_mail(content_list, debug_info):
    main_body = "".join(content_list) if content_list else f"<div style='color:red;'>⚠️ 诊断信息：{debug_info}</div>"
    
    html_layout = f"""
    <div style="font-family:sans-serif; max-width:600px; margin:auto; border:1px solid #eee; padding:20px; border-radius:10px;">
        <h2 style="color:#1a73e8; border-bottom:2px solid #1a73e8; padding-bottom:10px;">🚀 小游戏市场情报·雷达</h2>
        {main_body}
        <div style="font-size:11px; color:#aaa; margin-top:20px; text-align:center;">
            引擎: Gemini 1.5 Flash | 模式: 强力翻译 | 时间: {time.strftime("%Y-%m-%d %H:%M")}
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
        print(f"❌ 邮件发送失败: {e}")

# --- 4. 主运行程序 ---
if __name__ == "__main__":
    final_results = []
    debug_log = ""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/110.0.0.0'}

    for src in TARGET_SOURCES:
        try:
            print(f"📡 正在尝试抓取: {src['name']}...")
            r = requests.get(src['url'], headers=headers, timeout=30)
            
            # 解决 404/403 问题
            if r.status_code != 200:
                debug_log += f"[{src['name']} 状态码: {r.status_code}] "
                continue
            
            soup = BeautifulSoup(r.text, 'html.parser')
            # 兼容处理：寻找所有的 h2 或 h3 标签作为标题，提高成功率
            titles = [t.text.strip() for t in soup.find_all(['h2', 'h3'])[:10]]
            
            if titles:
                summary = ai_summarize("\n".join(titles), src['name'])
                if summary:
                    # 关键修复：不在 f-string 内部使用反斜杠，彻底解决语法错误
                    safe_summary = summary.replace('\n', '<br>')
                    section_content = f"<h3>📍 {src['name']}</h3><div style='font-size:14px; color:#444;'>{safe_summary}</div>"
                    final_results.append(section_content)
            else:
                debug_log += f"[{src['name']} 页面解析无标题] "
                
        except Exception as e:
            debug_log += f"[{src['name']} 报错: {str(e)[:30]}] "

    send_mail(final_results, debug_log if debug_log else "一切正常，但未发现小游戏匹配项")
