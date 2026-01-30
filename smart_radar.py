import os
import time
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
import smtplib
from email.mime.text import MIMEText
from email.header import Header

# --- 1. 配置区域 (从 GitHub Secrets 安全读取) ---
#
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
RECIPIENT_EMAIL = "tanweilin1987@gmail.com"
SENDER_EMAIL = os.environ.get('EMAIL_USER')
SENDER_PASS = os.environ.get('EMAIL_PASS')

TARGET_SOURCES = [
    {"name": "游戏日报", "url": "https://www.gamelook.com.cn/category/mini-game"},
    {"name": "游戏陀螺", "url": "https://www.youxituoluo.com/tag/%E5%B0%8F%E6%B8%B8%E6%88%8F"},
    {"name": "小红书-她按开始键", "url": "https://www.xiaohongshu.com/user/profile/5df0a6990000000001000695"},
    {"name": "DataEye报告", "url": "https://www.dataeye.com/report"}
]

# --- 2. AI 逻辑 (彻底修复 404 并增强时效性) ---
def ai_summarize(content):
    if not GEMINI_API_KEY: return "❌ 错误：未检测到 GEMINI_API_KEY，请检查 GitHub Secrets 配置"
    try:
        #
        # 修复点：强制指定 transport='rest' 绕过 v1beta 导致的 404 报错
        genai.configure(api_key=GEMINI_API_KEY, transport='rest')
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        #
        # 逻辑点：不再代码过滤日期，让 AI 从全文中提取“近一个月”的干货
        prompt = f"""
        你是一位资深游戏行业分析师。请从以下内容中提炼【近一个月内】的小游戏情报：
        1. 重点分析 2026年1月 的新题材、玩法趋势或爆款案例。
        2. 提炼出 3 条对开发者有实战参考价值的数据或商业建议。
        3. 忽略广告、无关链接和陈旧信息。
        
        待处理内容：
        {content[:4000]}
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"⚠️ AI 总结受阻：{str(e)}"

# --- 3. 邮件发送系统 ---
def send_mail(content_list):
    full_body = "".join(content_list)
    if not full_body.strip():
        #
        full_body = "<p style='color:orange;'>今日扫描完成，但各监控源暂无近期更新的小游戏深度内容。</p>"

    html_content = f"""
    <div style="font-family: sans-serif; max-width: 700px; margin: auto; border: 1px solid #eee; padding: 25px; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.05);">
        <h2 style="color: #1a73e8; border-bottom: 3px solid #1a73e8; padding-bottom: 10px; text-align: center;">🛡️ 小游戏·深度情报雷达</h2>
        <div style="line-height: 1.8; color: #333;">{full_body}</div>
        <div style="font-size: 11px; color: #aaa; text-align: center; margin-top: 30px; border-top: 1px solid #f0f0f0; padding-top: 15px;">
            监控时效：近 30 天 | 引擎：Gemini 1.5 Stable | 时间：{time.strftime('%Y-%m-%d %H:%M')}
        </div>
    </div>
    """
    msg = MIMEText(html_content, 'html', 'utf-8')
    msg['From'] = f"SmartRadar <{SENDER_EMAIL}>"
    msg['To'] = RECIPIENT_EMAIL
    msg['Subject'] = Header(f"📊 小游戏趋势内参 - {time.strftime('%m-%d')}", 'utf-8')
    
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASS)
            server.sendmail(SENDER_EMAIL, [RECIPIENT_EMAIL], msg.as_string())
        print("✅ 邮件发送成功")
    except Exception as e:
        print(f"❌ 邮件失败: {e}")

if __name__ == "__main__":
    final_results = []
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    for source in TARGET_SOURCES:
        try:
            r = requests.get(source['url'], headers=headers, timeout=20)
            soup = BeautifulSoup(r.text, 'html.parser')
            #
            # 逻辑点：抓取全文交给 AI 判断，不再做硬性的字符串日期筛选
            raw_text = soup.get_text(separator=' ', strip=True)
            summary = ai_summarize(raw_text)
            
            if len(summary) > 50:
                final_results.append(f"""
                <div style="margin-bottom: 20px; padding: 15px; background: #f9f9f9; border-left: 5px solid #1a73e8;">
                    <b style="color:#1a73e8;">📍 来源：{source['name']}</b><br>{summary.replace('\\n', '<br>')}
                </div><hr style="border:0; border-top:1px dashed #eee;">
                """)
        except: continue
    send_mail(final_results)
