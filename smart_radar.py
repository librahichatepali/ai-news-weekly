import os
import time
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
import smtplib
from email.mime.text import MIMEText
from email.header import Header

# --- 1. 配置区域 ---
# 必须像这样使用 os.environ.get，严禁在此粘贴任何 AIza 开头的字符串！
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
RECIPIENT_EMAIL = "tanweilin1987@gmail.com"
SENDER_EMAIL = os.environ.get('EMAIL_USER')
SENDER_PASS = os.environ.get('EMAIL_PASS')

TARGET_SOURCES = [
    {"name": "游戏日报", "url": "https://www.gamelook.com.cn/category/mini-game"},
    {"name": "小红书-她按开始键", "url": "https://www.xiaohongshu.com/user/profile/5df0a6990000000001000695"}
]

# --- 2. AI 逻辑 ---
def ai_summarize(content):
    if not GEMINI_API_KEY:
        return "❌ 错误：GitHub 未检测到 GEMINI_API_KEY 变量"
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(f"提炼小游戏题材干货：{content[:4000]}")
        return response.text
    except Exception as e:
        return f"⚠️ AI 报错详情: {str(e)}"

# --- 3. 邮件发送 ---
def send_mail(body):
    msg = MIMEText(body.replace('\n', '<br>'), 'html', 'utf-8')
    msg['From'] = f"SmartRadar <{SENDER_EMAIL}>"
    msg['To'] = RECIPIENT_EMAIL
    msg['Subject'] = Header(f"🔥 小游戏情报 - {time.strftime('%m-%d')}", 'utf-8')
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASS)
            server.sendmail(SENDER_EMAIL, [RECIPIENT_EMAIL], msg.as_string())
        print("✅ 发送成功")
    except Exception as e:
        print(f"❌ 发送失败: {e}")

if __name__ == "__main__":
    combined_content = ""
    for s in TARGET_SOURCES:
        try:
            r = requests.get(s['url'], timeout=15)
            txt = BeautifulSoup(r.text, 'html.parser').get_text()[:2000]
            combined_content += f"来自{s['name']}:\n{ai_summarize(txt)}\n\n"
        except: continue
    send_mail(combined_content if combined_content else "今日无更新")
