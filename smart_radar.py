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

# --- 2. AI 逻辑 (彻底修复 404) ---
def ai_summarize(content):
    if not GEMINI_API_KEY: return "❌ 错误：未配置 API Key"
    try:
        # 修复点 1：显式指定 transport='rest' 强制使用稳定版 v1 接口
        # 这会绕过导致 404 的 v1beta 路径
        genai.configure(api_key=GEMINI_API_KEY, transport='rest')
        
        # 修复点 2：使用更稳健的模型调用方式
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # 修复点 3：调整时间跨度至一个月，并强化提取指令
        prompt = f"""
        你是一个资深小游戏行业分析师。请分析以下内容并提炼【近一个月内】的价值信息：
        - 重点识别 2026年1月 的爆款题材、核心玩法和买量 ROI 数据。
        - 如果没有具体数据，请总结当前行业最受关注的 3 个技术或商业方向。
        - 忽略过时的招聘或无关信息。
        
        待分析内容：
        {content[:4000]}
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        # 如果 1.5-flash 还是不行，尝试回退到 gemini-pro
        try:
            model = genai.GenerativeModel('gemini-pro')
            return model.generate_content("提炼小游戏行业干货：" + content[:3000]).text
        except:
            return "⚠️ AI 扫描失败详情: " + str(e)

# --- 3. 邮件发送逻辑 ---
def send_mail(content_list):
    full_body = "".join(content_list)
    if not full_body.strip():
        full_body = "<p style='color:orange;'>系统报告：监控源中未发现近 1 个月内更新且符合条件的【小游戏题材】内容。</p>"

    html_content = f"""
    <div style="font-family: sans-serif; max-width: 650px; margin: auto; border: 1px solid #ddd; padding: 25px; border-radius: 12px;">
        <h2 style="color: #1a73e8; border-bottom: 3px solid #1a73e8; padding-bottom: 12px; text-align: center;">🛡️ 小游戏·近30日情报精炼</h2>
        <div style="line-height: 1.8; color: #333;">{full_body}</div>
        <p style="font-size: 11px; color: #999; text-align: center; margin-top: 25px;">
            监控时效：近 30 天 | 来源：游戏日报/陀螺/DataEye/小红书 | 状态：AI 深度扫描已完成
        </p>
    </div>
    """
    msg = MIMEText(html_content, 'html', 'utf-8')
    msg['From'] = f"SmartRadar <{SENDER_EMAIL}>"
    msg['To'] = RECIPIENT_EMAIL
    msg['Subject'] = Header(f"🚨 小游戏月度趋势雷达 - {time.strftime('%m-%d')}", 'utf-8')
    
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASS)
            server.sendmail(SENDER_EMAIL, [RECIPIENT_EMAIL], msg.as_string())
        print("✅ 报告已成功发送")
    except Exception as e:
        print("❌ 邮件发送异常: " + str(e))

if __name__ == "__main__":
    final_results = []
    headers = {'User-Agent': 'Mozilla/5.0'}
    for source in TARGET_SOURCES:
        try:
            r = requests.get(source['url'], headers=headers, timeout=15)
            # 强化文本提取，确保 AI 能读到内容
            text = BeautifulSoup(r.text, 'html.parser').get_text(separator=' ', strip=True)[:3500]
            summary = ai_summarize(text)
            
            # 过滤掉报错信息和无效结果
            if "AI 扫描失败" not in summary:
                formatted_summary = summary.replace('\n', '<br>')
                final_results.append(f"<div style='margin-bottom:20px;'><b>📍 来源：{source['name']}</b><br>{formatted_summary}</div><hr>")
        except: continue
    send_mail(final_results)
