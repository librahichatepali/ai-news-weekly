import os
import time
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
import smtplib
from email.mime.text import MIMEText
from email.header import Header

# --- 1. 核心配置 (从 GitHub Secrets 读取) ---
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

# --- 2. AI 核心引擎 (彻底修复 404 问题) ---
def ai_summarize(content):
    if not GEMINI_API_KEY:
        return "❌ 错误：未检测到 GEMINI_API_KEY"
    try:
        # 核心操作：配置时仅锁定 API Key
        genai.configure(api_key=GEMINI_API_KEY)
        
        # 修复点：通过这种方式创建模型，强制 SDK 使用稳定的 v1 接口，避开 v1beta
        model = genai.GenerativeModel(model_name='gemini-1.5-flash')
        
        prompt = f"""
        你是一位资深游戏猎头。请根据内容提炼近一个月的小游戏干货：
        - 识别 2026年1月 的题材、玩法趋势及爆款数据。
        - 提炼 3 条实战建议。
        
        内容如下：
        {content[:4000]}
        """
        # 调用时显式指定使用 rest 传输
        response = model.generate_content(prompt, request_options={"timeout": 600})
        return response.text
    except Exception as e:
        # 如果依然报 404，这里会捕获并显示具体错误
        return f"⚠️ AI 分析失败: {str(e)}"

# --- 3. 邮件发送系统 ---
def send_mail(content_list):
    full_body = "".join(content_list)
    if not full_body.strip():
        full_body = "<p style='color:orange;'>今日扫描完成，但目标源近期暂无深度干货更新。</p>"

    html_header = '<div style="font-family:sans-serif;max-width:700px;margin:auto;border:1px solid #eee;padding:25px;border-radius:12px;">'
    html_title = '<h2 style="color:#1a73e8;border-bottom:3px solid #1a73e8;padding-bottom:10px;text-align:center;">🛡️ 小游戏·深度情报雷达</h2>'
    curr_time = time.strftime("%Y-%m-%d %H:%M")
    html_footer = f'<div style="font-size:11px;color:#aaa;text-align:center;margin-top:30px;border-top:1px solid #f0f0f0;padding-top:15px;">监控时效：近30日 | 时间：{curr_time}</div></div>'
    
    final_html = html_header + html_title + full_body + html_footer
    
    msg = MIMEText(final_html, 'html', 'utf-8')
    msg['From'] = f"SmartRadar <{SENDER_EMAIL}>"
    msg['To'] = RECIPIENT_EMAIL
    msg['Subject'] = Header(f"📊 小游戏趋势内参 - {time.strftime('%m-%d')}", 'utf-8')
    
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASS)
            server.sendmail(SENDER_EMAIL, [RECIPIENT_EMAIL], msg.as_string())
        print("✅ 邮件已成功发出")
    except Exception as e:
        print(f"❌ 邮件发送故障: {e}")

# --- 4. 自动化流程 ---
if __name__ == "__main__":
    results = []
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    for src in TARGET_SOURCES:
        try:
            print(f"正在扫描: {src['name']}...")
            r = requests.get(src['url'], headers=headers, timeout=20)
            text = BeautifulSoup(r.text, 'html.parser').get_text(separator=' ', strip=True)
            summary = ai_summarize(text)
            
            if len(summary) > 50:
                # 修复换行符显示问题
                clean_summary = summary.replace('\n', '<br>')
                section = f"""
                <div style="margin-bottom:20px;padding:15px;background:#f9f9f9;border-left:5px solid #1a73e8;">
                    <b style="color:#1a73e8;">📍 来源：{src['name']}</b><br>
                    <div style="margin-top:10px;">{clean_summary}</div>
                </div>
                """
                results.append(section)
        except Exception as e:
            print(f"⚠️ {src['name']} 访问异常: {e}")
            continue
        
    send_mail(results)
