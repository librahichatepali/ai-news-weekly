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

# 混合源：如果一个 404，总有其他的能动
TARGET_SOURCES = [
    {"name": "GameRefinery (小游戏专家)", "url": "https://www.gamerefinery.com/feed/"},
    {"name": "MobileGamer.biz", "url": "https://mobilegamer.biz/feed/"},
    {"name": "PocketGamer", "url": "https://www.pocketgamer.com/news/"},
    {"name": "VentureBeat (游戏频道)", "url": "https://venturebeat.com/category/games/feed/"}
]

# --- 2. 强效 AI 翻译逻辑 ---
def ai_summarize(content, source_name):
    if not GEMINI_API_KEY: return "Error: API Key Missing"
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    # 彻底放开屏蔽词，禁止 AI 拒绝回答
    prompt = f"""
    任务：你是专业翻译。请从以下 {source_name} 的动态中，强行提取并翻译【4条】与“小游戏/移动游戏/排行榜”相关的内容。
    
    要求：
    1. 必须翻译成中文。
    2. 严禁回答“无深度资讯”、“无内容”或“未发现摘要”。
    3. 如果没有小游戏，就翻译该媒体最火的 4 条新闻标题。
    
    待翻译内容：
    {content}
    """
    
    try:
        response = requests.post(api_url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=60)
        res_json = response.json()
        return res_json["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        return f"AI 接口异常: {str(e)[:30]}"

# --- 3. 邮件发送：避开所有语法坑 ---
def send_mail(content_list, debug_info):
    # 彻底解决 f-string 里的反斜杠语法报错
    main_body = "".join(content_list)
    if not main_body:
        main_body = f"<div style='color:red;'>⚠️ 诊断日志：{debug_info}</div>"
    
    html_layout = f"""
    <div style="font-family:sans-serif; border:1px solid #eee; padding:20px; border-radius:10px;">
        <h2 style="color:#1a73e8; border-bottom:2px solid #1a73e8; padding-bottom:10px;">🧪 情报雷达·存活测试</h2>
        {main_body}
        <hr style="border:0; border-top:1px solid #eee; margin:20px 0;">
        <div style="font-size:12px; color:#aaa; text-align:center;">
            模式: 强制输出4条 | 状态: 屏蔽词已关闭 | 时间: {time.strftime("%Y-%m-%d %H:%M")}
        </div>
    </div>
    """
    
    msg = MIMEText(html_layout, 'html', 'utf-8')
    msg['From'] = f"SmartRadar <{SENDER_EMAIL}>"
    msg['To'] = RECIPIENT_EMAIL
    msg['Subject'] = Header(f"【测试】小游戏情报测试 - {time.strftime('%m-%d')}", 'utf-8')
    
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASS)
            server.sendmail(SENDER_EMAIL, [RECIPIENT_EMAIL], msg.as_string())
        print("✅ 邮件已发出")
    except Exception as e:
        print(f"❌ 发送失败: {e}")

# --- 4. 主逻辑：多路备份抓取 ---
if __name__ == "__main__":
    final_results = []
    global_debug = ""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/110.0.0.0'}

    for src in TARGET_SOURCES:
        try:
            print(f"📡 正在尝试抓取: {src['name']}...")
            r = requests.get(src['url'], headers=headers, timeout=25)
            
            if r.status_code != 200:
                global_debug += f"[{src['name']} Code {r.status_code}] "
                continue
                
            soup = BeautifulSoup(r.text, 'html.parser')
            # 兼容处理：寻找所有的标题标签
            titles = [t.text.strip() for t in soup.find_all(['title', 'h2', 'h3'])[:15]]
            
            if len(titles) > 2:
                raw_text = "\n".join(titles)
                summary = ai_summarize(raw_text, src['name'])
                if summary:
                    # 关键修复：不在 f-string 内部做 replace
                    safe_summary = summary.replace('\n', '<br>')
                    section = "<h3>📍 来自: " + src['name'] + "</h3><div>" + safe_summary + "</div>"
                    final_results.append(section)
            else:
                global_debug += f"[{src['name']} 解析内容过少] "
        except Exception as e:
            global_debug += f"[{src['name']} 异常: {str(e)[:20]}] "

    send_mail(final_results, global_debug if global_debug else "网络与 AI 均未返回有效内容")
