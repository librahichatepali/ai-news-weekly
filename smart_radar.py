import os
import time
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
import smtplib
from email.mime.text import MIMEText
from email.header import Header

# --- 1. 配置区域 ---
# 从 GitHub Secrets 安全读取配置
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
RECIPIENT_EMAIL = "tanweilin1987@gmail.com"
SENDER_EMAIL = os.environ.get('EMAIL_USER')
SENDER_PASS = os.environ.get('EMAIL_PASS')

# 监控目标：游戏日报、小红书博主
TARGET_SOURCES = [
    {"name": "游戏日报", "url": "https://www.gamelook.com.cn/category/mini-game"},
    {"name": "小红书-她按开始键", "url": "https://www.xiaohongshu.com/user/profile/5df0a6990000000001000695"}
]

# --- 2. AI 精炼逻辑 ---
def ai_summarize(content):
    if not GEMINI_API_KEY:
        return "错误：未配置 API Key"
    
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-pro')
    
    prompt = f"""
    你是一个资深的小游戏行业分析师。请阅读以下内容，并为忙碌的制作人提炼最核心的干货。
    要求：
    1. 剔除所有寒暄和废话。
    2. 重点输出：题材亮点、核心玩法、买量/消耗数据、行业趋势。
    3. 如果内容不涉及小游戏，直接返回“无相关内容”。
    
    待处理内容：
    {content[:3000]} 
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"AI 总结失败: {str(e)}"

# --- 3. 核心抓取与邮件逻辑 ---
def send_final_mail(content_text):
    # 修复语法错误：先在外部处理好换行符，避免在 f-string 中直接使用反斜杠
    html_body = content_text.replace('\n', '<br>')
    
    html_content = f"""
    <div style="font-family: sans-serif; max-width: 600px; margin: auto; border: 1px solid #eee; padding: 20px; border-radius: 10px;">
        <h2 style="color: #1a73e8; border-bottom: 2px solid #1a73e8; padding-bottom: 10px;">💎 今日小游戏精华内参</h2>
        <div style="line-height: 1.6; color: #333;">
            {html_body}
        </div>
        <p style="font-size: 11px; color: #999; margin-top: 30px; border-top: 1px dashed #ccc; padding-top: 10px;">
            注：本报告由 Gemini AI 自动精炼生成。
        </p>
    </div>
    """
    msg = MIMEText(html_content, 'html', 'utf-8')
    msg['From'] = f"SmartRadar <{SENDER_EMAIL}>"
    msg['To'] = RECIPIENT_EMAIL
    msg['Subject'] = Header(f"📊 小游戏情报精炼 - {time.strftime('%m-%d')}", 'utf-8')
    
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASS)
            server.sendmail(SENDER_EMAIL, [RECIPIENT_EMAIL], msg.as_string())
        print("✅ 指挥部邮件已送达")
    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")

def run_radar():
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0'}
    all_summaries = []

    for source in TARGET_SOURCES:
        try:
            resp = requests.get(source['url'], headers=headers, timeout=15)
            soup = BeautifulSoup(resp.text, 'html.parser')
            # 简单抓取逻辑：根据不同站点特征提取正文
            text_content = soup.get_text()
            summary = ai_summarize(text_content)
            
            if "无相关内容" not in summary:
                all_summaries.append(f"### 来自：{source['name']}\n{summary}\n")
        except Exception as e:
            print(f"❌ 抓取 {source['name']} 失败: {e}")

    if all_summaries:
        send_final_mail("\n".join(all_summaries))
    else:
        print("今日暂无符合条件的新题材")

if __name__ == "__main__":
    run_radar()
