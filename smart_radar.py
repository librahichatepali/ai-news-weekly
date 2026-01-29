import os
import time
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
import smtplib
from email.mime.text import MIMEText
from email.header import Header

# --- 1. 配置区域 ---
# 严格从 GitHub Secrets 读取
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
RECIPIENT_EMAIL = "tanweilin1987@gmail.com"
SENDER_EMAIL = os.environ.get('EMAIL_USER')
SENDER_PASS = os.environ.get('EMAIL_PASS')

TARGET_SOURCES = [
    {"name": "游戏日报", "url": "https://www.gamelook.com.cn/category/mini-game"},
    {"name": "小红书-她按开始键", "url": "https://www.xiaohongshu.com/user/profile/5df0a6990000000001000695"}
]

# --- 2. AI 精炼逻辑 ---
def ai_summarize(content):
    if not GEMINI_API_KEY:
        return "错误：GitHub Secrets 未检测到 API Key"
    
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        你是一个资深小游戏分析师。请分析以下内容并提炼 2026年1月 的最新行业干货。
        重点提取：题材亮点、玩法、买量/ROI数据。
        
        数据如下：
        {content[:5000]}
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"AI 调用失败（可能是 Key 权限问题）: {str(e)}"

# --- 3. 邮件发送逻辑 ---
def send_final_mail(content_text):
    html_body = content_text.replace('\n', '<br>')
    html_content = f"""
    <div style="font-family: sans-serif; max-width: 650px; margin: auto; padding: 20px; border: 1px solid #eee;">
        <h2 style="color: #1a73e8; border-bottom: 2px solid #1a73e8; padding-bottom: 10px;">📊 小游戏情报内参</h2>
        <div style="line-height: 1.6; color: #333;">{html_body}</div>
    </div>
    """
    msg = MIMEText(html_content, 'html', 'utf-8')
    msg['From'] = f"SmartRadar <{SENDER_EMAIL}>"
    msg['To'] = RECIPIENT_EMAIL
    msg['Subject'] = Header(f"🔥 小游戏爆款雷达 - {time.strftime('%m-%d')}", 'utf-8')
    
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASS)
            server.sendmail(SENDER_EMAIL, [RECIPIENT_EMAIL], msg.as_string())
        print("✅ 邮件已成功送达")
    except Exception as e:
        print(f"❌ 邮件发送异常: {e}")

# --- 4. 运行主函数 ---
def run_radar():
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    all_summaries = []

    for source in TARGET_SOURCES:
        try:
            resp = requests.get(source['url'], headers=headers, timeout=15)
            soup = BeautifulSoup(resp.text, 'html.parser')
            clean_text = soup.get_text(separator=' ', strip=True)[:3000]
            
            summary = ai_summarize(clean_text)
            if "无相关内容" not in summary:
                all_summaries.append(f"<b>【来自：{source['name']}】</b><br>{summary}<hr>")
        except:
            continue

    if all_summaries:
        send_final_mail("\n".join(all_summaries))
    else:
        send_final_mail("系统运行报告：今日已扫描，但暂未发现符合条件的题材更新。")

if __name__ == "__main__":
    run_radar()
