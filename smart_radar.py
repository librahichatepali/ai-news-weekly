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

# --- 2. AI 逻辑 (强化版) ---
def ai_summarize(content):
    if not GEMINI_API_KEY: return "❌ 错误：未检测到 Key"
    try:
        # 配置 API
        genai.configure(api_key=GEMINI_API_KEY)
        
        # 显式使用稳定版模型标识符
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # 核心 Prompt
        prompt = "请分析以下小游戏行业内容并提炼2026年1月的爆款题材、玩法创新和买量数据：" + content[:4000]
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return "⚠️ AI 总结暂时不可用: " + str(e)

# --- 3. 邮件发送逻辑 (修复反斜杠问题) ---
def send_mail(content_list):
    # 使用 join 拼接，避免在 f-string 中直接使用反斜杠
    full_body = "<hr>".join(content_list)
    if not full_body.strip():
        full_body = "系统运行正常，但今日监控源未解析到有效的小游戏题材更新。"

    html_content = f"""
    <div style="font-family: sans-serif; max-width: 650px; margin: auto; border: 1px solid #ddd; padding: 20px; border-radius: 10px;">
        <h2 style="color: #1a73e8; text-align: center; border-bottom: 2px solid #1a73e8; padding-bottom: 10px;">🚀 小游戏·实战内参</h2>
        <div style="line-height: 1.6; color: #333;">
            {full_body}
        </div>
        <p style="font-size: 12px; color: #999; text-align: center; margin-top: 20px;">
            监控日期：{time.strftime('%Y-%m-%d')} | 状态：AI 深度扫描已完成
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
        print("✅ 邮件已成功发送")
    except Exception as e:
        print("❌ 邮件发送失败: " + str(e))

# --- 4. 主运行流程 ---
if __name__ == "__main__":
    print("🔍 启动全网深度扫描...")
    final_results = []
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    for source in TARGET_SOURCES:
        try:
            print(f"正在读取: {source['name']}")
            r = requests.get(source['url'], headers=headers, timeout=15)
            soup = BeautifulSoup(r.text, 'html.parser')
            # 提取可见文本并精简
            text = soup.get_text(separator=' ', strip=True)[:3000]
            
            summary = ai_summarize(text)
            if "无相关内容" not in summary:
                # 预格式化内容，避免 HTML 渲染问题
                formatted_summary = summary.replace('\n', '<br>')
                final_results.append(f"<b>📍 来源：{source['name']}</b><br>{formatted_summary}")
        except Exception as e:
            print(f"抓取 {source['name']} 时出错: {e}")

    send_mail(final_results)
