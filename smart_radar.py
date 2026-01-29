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

# --- 2. AI 精炼逻辑 (修复 404 关键点) ---
def ai_summarize(content):
    if not GEMINI_API_KEY: return "错误：未配置 API Key"
    
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        # 核心修复：使用 gemini-1.5-flash，不带 -latest 后缀，这是目前最兼容的写法
        model = genai.GenerativeModel(model_name='gemini-1.5-flash') 
        
        prompt = f"""
        你是一个资深小游戏分析师。请分析以下内容并提炼 2026年1月 的最新行业干货。
        要求：
        1. 重点：题材亮点、核心玩法、买量/ROI数据。
        2. 即使只有标题，也请基于标题进行热点总结。
        
        数据如下：
        {content[:6000]}
        """
        # 强制指定版本参数，绕过 beta 版本的 404 限制
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        # 如果还是不行，说明可能是 API 权限问题，返回具体细节
        return f"AI 诊断：模型调用异常，请确认 API Key 是否已启用 Gemini 1.5 服务。细节: {str(e)}"

# --- 3. 邮件发送逻辑 ---
def send_final_mail(content_text):
    html_body = content_text.replace('\n', '<br>')
    html_content = f"""
    <div style="font-family: sans-serif; max-width: 650px; margin: auto; border: 1px solid #ddd; padding: 25px; border-radius: 12px; background-color: #fff;">
        <h2 style="color: #1a73e8; border-bottom: 3px solid #1a73e8; padding-bottom: 12px; text-align: center;">🛡️ 小游戏·情报内参</h2>
        <div style="line-height: 1.7; color: #333; padding: 10px;">
            {html_body}
        </div>
    </div>
    """
    msg = MIMEText(html_content, 'html', 'utf-8')
    msg['From'] = f"SmartRadar <{SENDER_EMAIL}>"
    msg['To'] = RECIPIENT_EMAIL
    msg['Subject'] = Header(f"📊 小游戏日报 - {time.strftime('%m-%d')}", 'utf-8')
    
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASS)
            server.sendmail(SENDER_EMAIL, [RECIPIENT_EMAIL], msg.as_string())
        print("✅ 邮件已送达")
    except Exception as e:
        print(f"❌ 邮件发送彻底失败: {e}")

# --- 4. 运行主函数 ---
def run_radar():
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0'}
    all_summaries = []

    for source in TARGET_SOURCES:
        try:
            print(f"🔍 正在穿透抓取: {source['name']}...")
            resp = requests.get(source['url'], headers=headers, timeout=20)
            soup = BeautifulSoup(resp.text, 'html.parser')
            # 暴力抓取前 3000 字，跳过复杂的选择器
            clean_text = soup.get_text(separator=' ', strip=True)[:3000]

            summary = ai_summarize(clean_text)
            if "无相关内容" not in summary:
                all_summaries.append(f"<b>【{source['name']}】</b><br>{summary}<hr>")
        except Exception as e:
            print(f"❌ {source['name']} 抓取失败")

    if all_summaries:
        send_final_mail("\n".join(all_summaries))
    else:
        send_final_mail("系统报告：今日已扫描，但未解析到新的爆款题材。")

if __name__ == "__main__":
    run_radar()
