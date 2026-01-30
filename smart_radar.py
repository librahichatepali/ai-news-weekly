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
    {"name": "MobileGamer.biz (行业专栏)", "url": "https://mobilegamer.biz/feed/"},
    {"name": "GameRefinery (市场趋势)", "url": "https://www.gamerefinery.com/feed/"}
]

# --- 2. AI 核心：不再进行“价值判定”，改为“强制翻译” ---
def ai_summarize(content, source_name):
    if not GEMINI_API_KEY: return ""
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    # 修改 Prompt：禁止 AI 判定“是否有价值”，强制翻译列表
    prompt = f"""
    任务：你是一个专业游戏翻译。请将来自 {source_name} 的新闻标题翻译成中文。
    要求：
    1. 简洁直接，按序号排列翻译后的列表。
    2. 只要有输入，就必须输出翻译内容，不得回复“无重大更新”。
    3. 不要包含任何自我介绍或结束语。
    
    待翻译列表：
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

# --- 3. 邮件发送系统：彻底修复保底变量名 ---
def send_mail(content_list, backup_titles):
    ai_output = "".join(content_list).strip()
    
    # 物理保底逻辑：即便 AI 接口失败，也确保显示抓取到的原始标题
    if not ai_output:
        # 使用修正后的变量名 all_captured_titles，解决 NameError
        backup_html = "<ul>" + "".join([f"<li>{t}</li>" for t in backup_titles]) + "</ul>"
        main_body = f"""
        <div style="padding:15px; background:#fff3cd; color:#856404; border-radius:8px; border:1px solid #ffeeba;">
            ⚠️ AI 今日未输出摘要，以下为为您抓取的原始标题列表：<br>{backup_html}
        </div>
        """
    else:
        main_body = ai_output

    html_layout = f"""
    <div style="font-family:sans-serif; max-width:650px; margin:auto; border:1px solid #eee; padding:25px; border-radius:15px; background:#fff;">
        <h2 style="color:#1a73e8; text-align:center; border-bottom:2px solid #1a73e8; padding-bottom:10px;">📡 每日游戏情报雷达</h2>
        <div style="line-height:1.8; color:#333;">{main_body}</div>
        <div style="font-size:12px; color:#aaa; text-align:center; margin-top:30px; border-top:1px solid #f0f0f0; padding-top:15px;">
            引擎: Gemini 1.5 Flash | 时间: {time.strftime("%Y-%m-%d %H:%M")}
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
        print("✅ 报告已成功发出")
    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")

# --- 4. 运行逻辑：解决变量定义报错 ---
if __name__ == "__main__":
    final_results = []
    all_captured_titles = [] # 修正变量名定义
    
    for src in TARGET_SOURCES:
        try:
            print(f"正在扫描: {src['name']}...")
            r = requests.get(src['url'], timeout=20)
            soup = BeautifulSoup(r.text, 'xml')
            items = soup.find_all('item')[:6] 
            
            raw_text = ""
            for it in items:
                title = it.find('title').text
                all_captured_titles.append(f"[{src['name']}] {title}")
                raw_text += f"- {title}\n"
            
            if raw_text:
                summary = ai_summarize(raw_text, src['name'])
                if summary:
                    # 预处理换行符，规避 HTML 渲染冲突
                    safe_summary = summary.replace('\n', '<br>')
                    section = f"""
                    <div style="margin-bottom:20px; padding:15px; background:#f8f9fa; border-left:5px solid #1a73e8;">
                        <b style="color:#1a73e8;">📍 {src['name']}</b><br>
                        <div style="margin-top:8px;">{safe_summary}</div>
                    </div>
                    """
                    final_results.append(section)
        except Exception as e:
            print(f"❌ {src['name']} 处理异常: {e}")
            
    send_mail(final_results, all_captured_titles)
