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

# --- 2. AI 核心：强制产出模式 ---
def ai_summarize(content, source_name):
    if not GEMINI_API_KEY: return ""
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    # 强制要求 AI 翻译，不再进行价值判断
    prompt = f"""
    任务：将以下来自 {source_name} 的游戏行业新闻标题翻译成中文。
    要求：
    1. 保持专业，按序号排列。
    2. 如果标题涉及厂商、新游、或数据，请加粗显示。
    3. 严禁回复“暂无动态”或类似废话。
    
    新闻列表：
    {content}
    """
    
    try:
        response = requests.post(api_url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=60)
        res_json = response.json()
        if "candidates" in res_json:
            return res_json["candidates"][0]["content"]["parts"][0]["text"]
        return ""
    except:
        return ""

# --- 3. 邮件系统：物理保底逻辑 ---
def send_mail(content_list, backup_titles):
    # 如果 AI 产出为空，则使用备份标题构建内容
    if not "".join(content_list).strip():
        backup_html = "<ul>" + "".join([f"<li>{t}</li>" for t in backup_titles]) + "</ul>"
        main_content = f"""
        <div style="padding:15px; background:#fff3cd; border-radius:8px; color:#856404;">
            ⚠️ AI 摘要生成失败，为您呈现原始抓取标题：<br>{backup_html}
        </div>
        """
    else:
        main_content = "".join(content_list)

    html_layout = f"""
    <div style="font-family:sans-serif; max-width:650px; margin:auto; border:1px solid #eee; padding:20px; border-radius:15px;">
        <h2 style="color:#1a73e8; text-align:center; border-bottom:2px solid #1a73e8; padding-bottom:10px;">📡 每日游戏趋势雷达</h2>
        <div style="line-height:1.7; color:#333;">{main_content}</div>
        <div style="font-size:12px; color:#999; text-align:center; margin-top:30px; border-top:1px solid #f0f0f0; padding-top:15px;">
            数据源: RSS Feed | 模式: 强力产出 | 时间: {time.strftime("%Y-%m-%d %H:%M")}
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
        print("✅ 报告已送达")
    except Exception as e:
        print(f"❌ 邮件失败: {e}")

# --- 4. 运行主逻辑 ---
if __name__ == "__main__":
    final_results = []
    backup_titles = []
    
    for src in TARGET_SOURCES:
        try:
            print(f"📡 扫描中: {src['name']}")
            r = requests.get(src['url'], timeout=20)
            soup = BeautifulSoup(r.text, 'xml')
            items = soup.find_all('item')[:5] # 每次只取 5 条最热动态
            
            raw_text = ""
            for it in items:
                t = it.find('title').text
                raw_text += f"- {t}\n"
                backup_titles.append(f"[{src['name']}] {t}")
            
            if raw_text:
                summary = ai_summarize(raw_text, src['name'])
                if summary:
                    # 预处理换行符，确保 HTML 渲染正常
                    safe_summary = summary.replace('\n', '<br>')
                    section = f"""
                    <div style="margin-bottom:20px; padding:15px; background:#f8f9fa; border-left:5px solid #1a73e8;">
                        <b style="color:#1a73e8;">📍 {src['name']}</b><br>
                        <div style="font-size:14px; margin-top:8px;">{safe_summary}</div>
                    </div>
                    """
                    final_results.append(section)
        except Exception as e:
            print(f"跳过 {src['name']}: {e}")
            
    send_mail(final_results, backup_titles)
