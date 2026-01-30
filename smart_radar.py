import os
import time
import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.header import Header

# --- 1. 配置 ---
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
RECIPIENT_EMAIL = "tanweilin1987@gmail.com"
SENDER_EMAIL = os.environ.get('EMAIL_USER')
SENDER_PASS = os.environ.get('EMAIL_PASS')

# 使用更简单的源进行压力测试
TARGET_SOURCES = [
    {"name": "Pocket Gamer", "url": "https://www.pocketgamer.biz/feed/"},
    {"name": "MobileGamer", "url": "https://mobilegamer.biz/feed/"}
]

# --- 2. 翻译官模式 AI ---
def ai_summarize(content, source_name):
    if not GEMINI_API_KEY: return "AI Key 缺失"
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    # 极简 Prompt，强制要求翻译前 4 条，无视任何筛选规则
    prompt = f"请直接将以下来自 {source_name} 的游戏新闻标题翻译成中文，强制列出 4 条，不要解释，不要说没内容：\n{content}"
    
    try:
        response = requests.post(api_url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=60)
        res_json = response.json()
        return res_json["candidates"][0]["content"]["parts"][0]["text"].strip()
    except:
        return ""

# --- 3. 稳健邮件函数 ---
def send_mail(content_list, debug_info):
    # 如果 content_list 为空，展示 debug_info 以排查是抓不到还是 AI 不干活
    main_body = "".join(content_list) if content_list else f"<p>抓取调试信息：{debug_info}</p>"
    
    html_layout = f"""
    <div style="font-family:sans-serif; border:1px solid #eee; padding:20px;">
        <h2 style="color:#1a73e8;">🛰️ 最终抓取测试报告</h2>
        {main_body}
        <p style="font-size:12px; color:#aaa; margin-top:20px;">时间: {time.strftime("%Y-%m-%d %H:%M")}</p>
    </div>
    """
    
    msg = MIMEText(html_layout, 'html', 'utf-8')
    msg['From'] = f"SmartRadar <{SENDER_EMAIL}>"
    msg['To'] = RECIPIENT_EMAIL
    msg['Subject'] = Header(f"【能力测试】情报抓取 - {time.strftime('%m-%d')}", 'utf-8')
    
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASS)
            server.sendmail(SENDER_EMAIL, [RECIPIENT_EMAIL], msg.as_string())
        print("✅ 邮件已发出")
    except Exception as e:
        print(f"❌ 发送失败: {e}")

# --- 4. 主逻辑：增加 User-Agent 伪装 ---
if __name__ == "__main__":
    final_results = []
    debug_log = ""
    
    # 模拟浏览器 Header，防止被网站屏蔽
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

    for src in TARGET_SOURCES:
        try:
            print(f"📡 尝试访问: {src['name']}...")
            r = requests.get(src['url'], headers=headers, timeout=30)
            
            # 检查是否成功获取内容
            if r.status_code != 200:
                debug_log += f"[{src['name']} 访问失败: Code {r.status_code}] "
                continue
                
            soup = BeautifulSoup(r.text, 'xml')
            items = soup.find_all('item')[:5]
            
            titles = [it.find('title').text for it in items if it.find('title')]
            
            if titles:
                raw_text = "\n".join(titles)
                summary = ai_summarize(raw_text, src['name'])
                if summary:
                    final_results.append(f"<h3>📍 {src['name']}</h3><p>{summary.replace('\n', '<br>')}</p>")
            else:
                debug_log += f"[{src['name']} 解析标题为空] "
                
        except Exception as e:
            debug_log += f"[{src['name']} 报错: {str(e)[:50]}] "
            
    send_mail(final_results, debug_log if debug_log else "未发现抓取异常，请检查 AI 内容")
