import os
import time
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
import smtplib
from email.mime.text import MIMEText
from email.header import Header

# --- 1. 配置区域 ---
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
    if not GEMINI_API_KEY: return "❌ 错误：未检测到 Key"
    try:
        # 核心修复：显式配置 API 版本为 v1 (稳定版)
        genai.configure(api_key=GEMINI_API_KEY, transport='rest') 
        
        # 使用确定的稳定模型名称
        model = genai.GenerativeModel(model_name='gemini-1.5-flash')
        
        prompt = f"分析以下小游戏行业内容并提炼 2026年1月 的干货：{content[:4000]}"
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        # 如果 1.5-flash 还是 404，尝试回退到 gemini-pro
        try:
            model = genai.GenerativeModel(model_name='gemini-pro')
            return model.generate_content(f"提炼干货：{content[:3000]}").text
        except:
            return f"⚠️ AI 报错详情: {str(e)}"

# --- 3. 邮件逻辑 ---
def send_mail(body):
    if not body.strip(): body = "今日监控源无符合条件的更新。"
    msg = MIMEText(body.replace('\n', '<br>'), 'html', 'utf-8')
    msg['From'] = f"SmartRadar <{SENDER_EMAIL}>"
    msg['To'] = RECIPIENT_EMAIL
    msg['Subject'] = Header(f"📊 小游戏日报 - {time.strftime('%m-%d')}", 'utf-8')
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASS)
            server.sendmail(SENDER_EMAIL, [RECIPIENT_EMAIL], msg.as_string())
        print("✅ 邮件发送成功")
    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")

if __name__ == "__main__":
    results = []
    headers = {'User-Agent': 'Mozilla/5.0'}
    for s in TARGET_SOURCES:
        try:
            r = requests.get(s['url'], headers=headers, timeout=15)
            # 暴力提取文字，增加容错
            soup = BeautifulSoup(r.text, 'html.parser')
            txt = soup.get_text(separator=' ', strip=True)[:3000]
            summary = ai_summarize(txt)
            results.append(f"<b>【{s['name']}】</b><br>{summary}<hr>")
        except: continue
    send_mail("".join(results))
