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

# 扩展监控源，增加成功率
TARGET_SOURCES = [
    {"name": "游戏日报", "url": "https://www.gamelook.com.cn/category/mini-game"},
    {"name": "游戏陀螺", "url": "https://www.youxituoluo.com/tag/%E5%B0%8F%E6%B8%B8%E6%88%8F"},
    {"name": "小红书-她按开始键", "url": "https://www.xiaohongshu.com/user/profile/5df0a6990000000001000695"}
]

# --- 2. AI 逻辑 (解决 404 关键) ---
def ai_summarize(content):
    if not GEMINI_API_KEY: return "❌ 未配置 API Key"
    try:
        # 强制指定 v1 稳定版接口，解决 404 models not found 问题
        genai.configure(api_key=GEMINI_API_KEY, transport='rest')
        
        # 优先使用 flash 模型
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        你是一个资深小游戏专家。请根据以下内容提炼【近一个月】的小游戏行业干货：
        1. 爆款题材与玩法趋势。
        2. 具体的买量或 ROI 数据（如有）。
        3. 对开发者的 3 条核心建议。
        待分析内容：{content[:4500]}
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        # 自动降级到 pro 模型
        try:
            model = genai.GenerativeModel('gemini-pro')
            return model.generate_content("提炼内容中的小游戏趋势：" + content[:3000]).text
        except:
            return "⚠️ AI 扫描失败: " + str(e)

# --- 3. 邮件发送逻辑 ---
def send_mail(content_list):
    full_body = "".join(content_list)
    if not full_body.strip():
        full_body = "<p style='color:orange;'>系统提示：今日扫描完成，但目标站点暂无任何可解析的小游戏内容。</p>"

    html_content = f"""
    <div style="font-family: sans-serif; max-width: 700px; margin: auto; border: 1px solid #ddd; padding: 25px; border-radius: 12px;">
        <h2 style="color: #1a73e8; border-bottom: 3px solid #1a73e8; padding-bottom: 15px; text-align: center;">🔥 小游戏·实战内参 (近30日合集)</h2>
        <div style="line-height: 1.8; color: #333;">{full_body}</div>
        <p style="font-size: 11px; color: #999; text-align: center; margin-top: 25px;">
            监控范围：近一个月 | 引擎：Gemini 1.5 Stable | 时间：{time.strftime('%Y-%m-%d')}
        </p>
    </div>
    """
    msg = MIMEText(html_content, 'html', 'utf-8')
    msg['From'] = f"SmartRadar <{SENDER_EMAIL}>"
    msg['To'] = RECIPIENT_EMAIL
    msg['Subject'] = Header(f"📊 小游戏月度趋势雷达 - {time.strftime('%m-%d')}", 'utf-8')
    
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASS)
            server.sendmail(SENDER_EMAIL, [RECIPIENT_EMAIL], msg.as_string())
        print("✅ 报告已送达")
    except Exception as e:
        print("❌ 发送失败: " + str(e))

if __name__ == "__main__":
    final_results = []
    headers = {'User-Agent': 'Mozilla/5.0'}
    for source in TARGET_SOURCES:
        try:
            r = requests.get(source['url'], headers=headers, timeout=20)
            # 抓取全文，不再做硬性的日期比对
            text = BeautifulSoup(r.text, 'html.parser').get_text(separator=' ', strip=True)
            summary = ai_summarize(text)
            
            if "AI 扫描失败" not in summary:
                formatted_summary = summary.replace('\n', '<br>')
                final_results.append(f"<div style='margin-bottom:20px;'><b>📍 来源：{source['name']}</b><br>{formatted_summary}</div><hr>")
        except: continue
    send_mail(final_results)
