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
    {"name": "Pocket Gamer", "url": "https://www.pocketgamer.biz/feed/"},
    {"name": "MobileGamer.biz", "url": "https://mobilegamer.biz/feed/"},
    {"name": "GameRefinery", "url": "https://www.gamerefinery.com/feed/"}
]

# --- 2. AI 核心：不再进行“深度”筛选，改为“全量翻译” ---
def ai_summarize(content, source_name):
    if not GEMINI_API_KEY: return ""
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    # 强制 AI 翻译所有标题
    prompt = f"""
    任务：你是一个游戏行业翻译官。请将来自 {source_name} 的新闻标题翻译成中文。
    要求：简洁明了，直接列出翻译后的列表即可。不要回复“没有内容”。
    
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

# --- 3. 邮件发送系统：修复保底显示逻辑 ---
def send_mail(content_list, backup_titles):
    # 检查 AI 产出是否真的有效
    ai_output = "".join(content_list).strip()
    
    if not ai_output:
        # 如果 AI 没说话，强制显示原始抓取的标题
        backup_html = "<ul style='color:#666;'>" + "".join([f"<li>{t}</li>" for t in backup_titles]) + "</ul>"
        main_body = f"""
        <div style="padding:15px; background:#fff3cd; border:1px solid #ffeeba; border-radius:8px;">
            <b style="color:#856404;">⚠️ AI 摘要生成跳过，以下为今日实时抓取标题：</b><br>
            {backup_html}
        </div>
        """
    else:
        main_body = ai_output

    html_layout = f"""
    <div style="font-family:sans-serif; max-width:650px; margin:auto; border:1px solid #eee; padding:25px; border-radius:15px; background:#fff;">
        <h2 style="color:#1a73e8; text-align:center; border-bottom:2px solid #1a73e8; padding-bottom:10px;">🎮 游戏行业·每日雷达</h2>
        <div style="line-height:1.8; color:#333;">{main_body}</div>
        <div style="font-size:12px; color:#aaa; text-align:center; margin-top:30px; border-top:1px solid #f0f0f0; padding-top:15px;">
            引擎: Gemini 1.5 Flash | 模式: 强力播报 | 时间: {time.strftime("%Y-%m-%d %H:%M")}
        </div>
    </div>
    """
    
    msg = MIMEText(html_layout, 'html', 'utf-8')
    msg['From'] = f"SmartRadar <{SENDER_EMAIL}>"
    msg['To'] = RECIPIENT_EMAIL
    msg['Subject'] = Header(f"📊 趋势探测报告 - {time.strftime('%m-%d')}", 'utf-8')
    
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASS)
            server.sendmail(SENDER_EMAIL, [RECIPIENT_EMAIL], msg.as_string())
        print("✅ 邮件已发送")
    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")

# --- 4. 运行主逻辑 ---
if __name__ == "__main__":
    final_results = []
    all_captured_titles = []
    
    for src in TARGET_SOURCES:
        try:
            print(f"正在拉取: {src['name']}")
            r = requests.get(src['url'], timeout=20)
            soup = BeautifulSoup(r.text, 'xml')
            items = soup.find_all('item')[:6] # 每次获取最新 6 条
            
            feed_content = ""
            for it in items:
                title = it.find('title').text
                all_captured_titles.append(f"[{src['name']}] {title}")
                feed_content += f"- {title}\n"
            
            if feed_content:
                summary = ai_summarize(feed_content, src['name'])
                if summary:
                    # 将换行符转换为 HTML 换行，防止在 f-string 中直接处理
                    formatted_summary = summary.replace('\n', '<br>')
                    section = f"""
                    <div style="margin-bottom:20px; padding:15px; background:#f8f9fa; border-left:5px solid #1a73e8;">
                        <b style="color:#1a73e8;">📍 {src['name']}</b><br>
                        <div style="margin-top:8px;">{formatted_summary}</div>
                    </div>
                    """
                    final_results.append(section)
        except Exception as e:
            print(f"源 {src['name']} 异常: {e}")
            
    send_mail(final_results, all_captured_titles)
