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

# --- 2. AI 总结逻辑 ---
def ai_summarize(content):
    if not GEMINI_API_KEY: return "❌ 错误：API Key 未配置"
    try:
        # 强制使用 v1 稳定版接口，解决 404 顽疾
        genai.configure(api_key=GEMINI_API_KEY, transport='rest')
        model = genai.GenerativeModel(model_name='gemini-1.5-flash')
        
        # 调整提示词：不再死磕“今天”，而是分析“近期”
        prompt = f"""
        你是一个资深小游戏行业专家。请根据以下抓取到的内容，提炼近一个月的行业价值情报：
        1. 总结核心的小游戏【题材】和【玩法】趋势。
        2. 如果有提到具体的【投放数据】或【ROI】，请重点列出。
        3. 如果内容较杂，请精炼出 3 条对开发者最有价值的建议。
        
        抓取内容：
        {content[:4000]}
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return "⚠️ AI 扫描提示: " + str(e)

# --- 3. 邮件发送逻辑 ---
def send_mail(content_list):
    full_body = "".join(content_list)
    if not full_body.strip():
        full_body = "<p style='color:orange;'>系统提示：今日扫描完成，但目标站点暂无任何可解析的小游戏内容。</p>"

    html_content = f"""
    <div style="font-family: sans-serif; max-width: 700px; margin: auto; border: 1px solid #ddd; padding: 25px; border-radius: 12px;">
        <h2 style="color: #1a73e8; border-bottom: 3px solid #1a73e8; padding-bottom: 15px; text-align: center;">🔥 小游戏·实战内参 (近期合集)</h2>
        <div style="line-height: 1.8; color: #333;">
            {full_body}
        </div>
        <p style="font-size: 11px; color: #999; text-align: center; margin-top: 25px; border-top: 1px solid #eee; padding-top: 10px;">
            监控范围：近30日动态 | 引擎：Gemini 1.5 Stable | 时间：{time.strftime('%Y-%m-%d %H:%M')}
        </p>
    </div>
    """
    msg = MIMEText(html_content, 'html', 'utf-8')
    msg['From'] = f"SmartRadar <{SENDER_EMAIL}>"
    msg['To'] = RECIPIENT_EMAIL
    msg['Subject'] = Header(f"📊 小游戏雷达 - 深度分析报告 - {time.strftime('%m-%d')}", 'utf-8')
    
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASS)
            server.sendmail(SENDER_EMAIL, [RECIPIENT_EMAIL], msg.as_string())
        print("✅ 报告已送达")
    except Exception as e:
        print("❌ 邮件发送失败: " + str(e))

# --- 4. 运行主函数 ---
if __name__ == "__main__":
    final_results = []
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    for source in TARGET_SOURCES:
        try:
            print(f"正在扫描: {source['name']}...")
            r = requests.get(source['url'], headers=headers, timeout=20)
            soup = BeautifulSoup(r.text, 'html.parser')
            # 提取所有可见文本，不做严格的“今天”时间筛选
            text = soup.get_text(separator=' ', strip=True)
            
            summary = ai_summarize(text)
            if len(summary) > 50:
                formatted_summary = summary.replace('\n', '<br>')
                final_results.append(f"""
                <div style="margin-bottom: 20px; padding: 15px; background-color: #f9f9f9; border-left: 5px solid #1a73e8;">
                    <b style="color: #1a73e8;">📍 来源：{source['name']}</b><br>
                    <div style="margin-top: 8px;">{formatted_summary}</div>
                </div>
                """)
        except: continue

    send_mail(final_results)
