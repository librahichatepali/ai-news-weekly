import os
import time
import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.header import Header

# --- 1. 配置区域 ---
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
RECIPIENT_EMAIL = "tanweilin1987@gmail.com"
SENDER_EMAIL = os.environ.get('EMAIL_USER')
SENDER_PASS = os.environ.get('EMAIL_PASS')

# 改用 RSS 源：格式统一、无广告、无 Cookie 干扰
TARGET_SOURCES = [
    {"name": "Pocket Gamer RSS", "url": "https://www.pocketgamer.biz/feed/"},
    {"name": "MobileGamer.biz RSS", "url": "https://mobilegamer.biz/feed/"},
    {"name": "GameRefinery Blog", "url": "https://www.gamerefinery.com/feed/"}
]

# --- 2. AI 核心：注入来源 Context ---
def ai_summarize(content, source_name):
    if not GEMINI_API_KEY: return "❌ 错误：未配置 Key"
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    prompt = f"""
    作为专业的游戏行业分析师，请从以下来自 {source_name} 的新闻列表中，挑选出今日最值得关注的 3 条动态。
    要求：
    - 优先选择：新游上线/测试、厂商收购、投融资、重大市场数据。
    - 用中文简明扼要地总结。
    - 如果没有实质新闻内容，请回复：今日暂无重大更新。
    
    新闻列表：
    {content[:15000]}
    """
    
    try:
        response = requests.post(api_url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=60)
        res_json = response.json()
        if "candidates" in res_json:
            return res_json["candidates"][0]["content"]["parts"][0]["text"]
        return "今日暂无重大更新"
    except Exception:
        return "⚠️ AI 响应超时"

# --- 3. 邮件系统：确保语法结构闭合 ---
def send_mail(content_list):
    combined_body = "".join(content_list)
    status_msg = ""
    
    # 状态可视化：区分“代码故障”与“内容为空”
    if not combined_body.strip():
        status_msg = """
        <div style="padding:15px; border:1px dashed #ffa500; color:#856404; background:#fff3cd; border-radius:10px; margin-bottom:20px;">
            📡 <b>探测简报：</b> RSS 链路畅通，但 AI 判定今日暂无符合标准的行业深度动态。
        </div>
        """

    html_layout = f"""
    <div style="font-family:sans-serif;max-width:700px;margin:auto;border:1px solid #ddd;padding:30px;border-radius:15px;">
        <h2 style="color:#1a73e8;text-align:center;border-bottom:4px solid #1a73e8;padding-bottom:12px;">🌍 全球游戏动态·RSS 探测报告</h2>
        {status_msg}
        <div style="line-height:1.7;color:#333;">{combined_body}</div>
        <div style="font-size:12px;color:#999;text-align:center;margin-top:40px;border-top:1px solid #eee;padding-top:20px;">
            验证状态：RSS 模式 | 引擎：Gemini 1.5 Flash | 时间：{time.strftime("%Y-%m-%d %H:%M")}
        </div>
    </div>
    """
    
    msg = MIMEText(html_layout, 'html', 'utf-8')
    msg['From'] = f"SmartRadar <{SENDER_EMAIL}>"
    msg['To'] = RECIPIENT_EMAIL
    msg['Subject'] = Header(f"📊 探测报告 - {time.strftime('%m-%d')}", 'utf-8')
    
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASS)
            server.sendmail(SENDER_EMAIL, [RECIPIENT_EMAIL], msg.as_string())
        print("✅ 探测报告已成功送达")
    except Exception as e:
        print(f"❌ 邮件发送异常: {e}")

# --- 4. 执行流程 ---
if __name__ == "__main__":
    results = []
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    for src in TARGET_SOURCES:
        try:
            print(f"正在扫描 RSS: {src['name']}...")
            r = requests.get(src['url'], headers=headers, timeout=20)
            soup = BeautifulSoup(r.text, 'xml') # RSS 使用 XML 解析
            items = soup.find_all('item')[:10] 
            
            feed_content = ""
            for it in items:
                title = it.find('title').get_text() if it.find('title') else ""
                desc = it.find('description').get_text() if it.find('description') else ""
                feed_content += f"- Title: {title}\n  Summary: {desc}\n\n"
            
            if len(feed_content) > 50:
                summary = ai_summarize(feed_content, src['name'])
                if "今日暂无重大更新" not in summary:
                    section = f"""
                    <div style="margin-bottom:25px;padding:20px;background:#f9f9f9;border-left:5px solid #1a73e8;">
                        <b style="color:#1a73e8;font-size:16px;">📍 来源：{src['name']}</b><br>
                        <div style="margin-top:10px;font-size:14px;color:#444;">{summary.replace('\n', '<br>')}</div>
                    </div>
                    """
                    results.append(section)
        except Exception as e:
            print(f"跳过 {src['name']}: {e}")
            
    send_mail(results)
