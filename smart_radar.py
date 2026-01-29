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
    {"name": "游戏陀螺", "url": "https://www.youxituoluo.com/tag/%E5%B0%8F%E6%B8%B8%E6%88%8F"},
    {"name": "小红书-她按开始键", "url": "https://www.xiaohongshu.com/user/profile/5df0a6990000000001000695"}
]

# --- 2. AI 逻辑 (强制 v1 稳定版) ---
def ai_summarize(content):
    if not GEMINI_API_KEY: return "❌ 错误：未检测到 Key"
    try:
        # 核心修复：显式指定 API 版本为 v1，避免 v1beta 导致的 404 错误
        genai.configure(api_key=GEMINI_API_KEY, transport='rest')
        
        # 强制指定模型，并清理可能引起干扰的后缀
        model = genai.GenerativeModel(model_name='models/gemini-1.5-flash')
        
        prompt = "提炼2026年1月小游戏爆款题材与买量数据：" + content[:4000]
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        # 如果 1.5-flash 还是失败，尝试回退到基础版 gemini-pro
        try:
            model = genai.GenerativeModel(model_name='models/gemini-pro')
            return model.generate_content("分析内容：" + content[:3000]).text
        except:
            return "⚠️ AI 诊断报告: " + str(e)

# --- 3. 邮件发送逻辑 ---
def send_mail(content_list):
    full_body = "<hr>".join(content_list)
    if not full_body.strip():
        full_body = "系统报告：已完成扫描，但今日监控源未解析到符合条件的内容。"

    html_content = f"""
    <div style="font-family: sans-serif; max-width: 650px; margin: auto; border: 1px solid #eee; padding: 25px; border-radius: 12px; background-color: #fdfdfd;">
        <h2 style="color: #1a73e8; border-bottom: 3px solid #1a73e8; padding-bottom: 12px; text-align: center;">🛡️ 小游戏·核心内参</h2>
        <div style="line-height: 1.8; color: #333;">{full_body}</div>
        <p style="font-size: 12px; color: #999; text-align: center; border-top: 1px solid #eee; padding-top: 15px;">
            监控时间：{time.strftime('%Y-%m-%d %H:%M')} | 引擎：Gemini 1.5 Stable
        </p>
    </div>
    """
    msg = MIMEText(html_content, 'html', 'utf-8')
    msg['From'] = f"SmartRadar <{SENDER_EMAIL}>"
    msg['To'] = RECIPIENT_EMAIL
    msg['Subject'] = Header(f"📊 小游戏雷达报告 - {time.strftime('%m-%d')}", 'utf-8')
    
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASS)
            server.sendmail(SENDER_EMAIL, [RECIPIENT_EMAIL], msg.as_string())
        print("✅ 邮件发送成功")
    except Exception as e:
        print("❌ 邮件发送失败: " + str(e))

# --- 4. 执行流程 ---
if __name__ == "__main__":
    final_results = []
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    for source in TARGET_SOURCES:
        try:
            r = requests.get(source['url'], headers=headers, timeout=15)
            soup = BeautifulSoup(r.text, 'html.parser')
            # 强化文本提取，确保 AI 能读到东西
            text = soup.get_text(separator=' ', strip=True)[:3500]
            
            summary = ai_summarize(text)
            # 过滤掉报错信息
            if "AI 诊断报告" not in summary:
                formatted_summary = summary.replace('\n', '<br>')
                final_results.append(f"<b>📍 来源：{source['name']}</b><br>{formatted_summary}")
        except: continue

    send_mail(final_results)
