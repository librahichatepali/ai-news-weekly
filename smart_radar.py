import os
import time
import datetime
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

# 监控目标
TARGET_SOURCES = [
    {"name": "游戏日报", "url": "https://www.gamelook.com.cn/category/mini-game"},
    {"name": "游戏陀螺", "url": "https://www.youxituoluo.com/tag/%E5%B0%8F%E6%B8%B8%E6%88%8F"},
    {"name": "小红书-她按开始键", "url": "https://www.xiaohongshu.com/user/profile/5df0a6990000000001000695"}
]

# --- 2. AI 精炼逻辑 ---
def ai_summarize(content):
    if not GEMINI_API_KEY: return "错误：未配置 API Key"
    genai.configure(api_key=GEMINI_API_KEY)
    
    # 修正：使用更兼容的模型名称标识符
    try:
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        
        prompt = f"""
        你是一个资深小游戏分析师。请分析以下内容并提炼 2026年1月 的最新行业干货：
        1. 题材亮点、核心玩法、买量/ROI数据。
        2. 剔除废话。即使只有标题，也请基于标题进行热点趋势总结。
        3. 如果内容完全不相关，返回“无相关内容”。

        待处理数据：
        {content[:8000]}
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"AI 总结失败，请检查 API 配置。错误详情: {str(e)}"

# --- 3. 邮件发送逻辑 ---
def send_final_mail(content_text):
    html_body = content_text.replace('\n', '<br>')
    html_content = f"""
    <div style="font-family: sans-serif; max-width: 650px; margin: auto; border: 1px solid #ddd; padding: 25px; border-radius: 12px;">
        <h2 style="color: #1a73e8; border-bottom: 3px solid #1a73e8; padding-bottom: 12px; text-align: center;">🚀 小游戏·实战内参 (2026版)</h2>
        <div style="line-height: 1.7; color: #333; padding: 10px;">
            {html_body}
        </div>
    </div>
    """
    msg = MIMEText(html_content, 'html', 'utf-8')
    msg['From'] = f"SmartRadar <{SENDER_EMAIL}>"
    msg['To'] = RECIPIENT_EMAIL
    msg['Subject'] = Header(f"🔥 小游戏情报精炼 - {time.strftime('%m-%d')}", 'utf-8')
    
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASS)
            server.sendmail(SENDER_EMAIL, [RECIPIENT_EMAIL], msg.as_string())
        print("✅ 邮件已送达")
    except Exception as e:
        print(f"❌ 发送失败: {e}")

# --- 4. 运行主函数 ---
def run_radar():
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0'}
    all_summaries = []

    for source in TARGET_SOURCES:
        try:
            print(f"🔍 扫描: {source['name']}...")
            resp = requests.get(source['url'], headers=headers, timeout=20)
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # 使用更通用的文字提取方式
            clean_text = soup.get_text(separator=' ', strip=True)[:4000]

            summary = ai_summarize(clean_text)
            if "无相关内容" not in summary:
                all_summaries.append(f"<b>📍 来源：{source['name']}</b><br>{summary}<br>")
        except Exception as e:
            print(f"❌ {source['name']} 扫描异常")

    if all_summaries:
        send_final_mail("\n".join(all_summaries))
    else:
        send_final_mail("系统运行正常，但今日监控源未提取到有效的文字内容。")

if __name__ == "__main__":
    run_radar()
