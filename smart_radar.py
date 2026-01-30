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

TARGET_SOURCES = [
    {"name": "Pocket Gamer", "url": "https://www.pocketgamer.biz/news/"},
    {"name": "GameRefinery", "url": "https://www.gamerefinery.com/blog/"},
    {"name": "MobileGamer", "url": "https://mobilegamer.biz/news/"}
]

# --- 2. AI 核心：强化新闻嗅觉 ---
def ai_summarize(content, source_name):
    if not GEMINI_API_KEY: return "❌ 未配置 Key"
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    prompt = f"""
    作为移动游戏分析师，请从 {source_name} 的网页文本中提取今日最值得关注的 2-3 条动态。
    忽略：隐私政策、登录、广告、作者介绍。
    重点提取：新游测试、大厂动态、收购、投融资。
    如果没有明确新闻，请仅回复：今日暂无重大更新。
    
    文本内容：
    {content[:12000]}
    """
    
    try:
        response = requests.post(api_url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=60)
        res_json = response.json()
        if "candidates" in res_json:
            return res_json["candidates"][0]["content"]["parts"][0]["text"]
        return "今日暂无重大更新"
    except:
        return "⚠️ API 访问波动"

# --- 3. 邮件发送：修复语法断裂 & 样式优化 ---
def send_mail(content_list):
    combined_body = "".join(content_list)
    
    # 彻底闭合所有括号和引号，防止 SyntaxError
    html_layout = f"""
    <div style="font-family:sans-serif;max-width:700px;margin:auto;border:1px solid #ddd;padding:30px;border-radius:15px;">
        <h2 style="color:#1a73e8;text-align:center;border-bottom:4px solid #1a73e8;padding-bottom:12px;">🌍 游戏趋势探测</h2>
        <div style="line-height:1.7;color:#333;">{combined_body if combined_body else '<p>📡 今日各源暂无深度更新，探测器一切正常。</p>'}</div>
        <div style="font-size:11px;color:#999;text-align:center;margin-top:40px;border-top:1px solid #eee;padding-top:20px;">
            验证：列表页解析+逻辑闭合 | 引擎：Gemini 1.5 Flash | 时间：{time.strftime("%Y-%m-%d %H:%M")}
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
            server.send_mail_string = msg.as_string() # 确保变量名正确
            server.sendmail(SENDER_EMAIL, [RECIPIENT_EMAIL], msg.as_string())
        print("✅ 邮件已成功发送")
    except Exception as e:
        print(f"❌ 发送异常: {e}")

# --- 4. 运行逻辑：深度清洗 ---
if __name__ == "__main__":
    results = []
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    for src in TARGET_SOURCES:
        try:
            print(f"扫描中: {src['name']}")
            r = requests.get(src['url'], headers=headers, timeout=25)
            r.encoding = r.apparent_encoding # 解决潜在乱码
            soup = BeautifulSoup(r.text, 'html.parser')
            
            # 精准摘除：剔除非内容区域，显著降低 AI 噪音
            for noise in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'noscript', 'form']):
                noise.decompose()
            
            clean_text = soup.get_text(separator=' ', strip=True)
            summary = ai_summarize(clean_text, src['name'])
            
            if "今日暂无重大更新" not in summary and len(summary) > 25:
                # 在进入 f-string 前处理换行，防止反斜杠冲突
                safe_summary = summary.replace('\n', '<br>')
                results.append(f"""
                <div style="margin-bottom:20px;padding:15px;background:#fdfdfd;border-left:4px solid #1a73e8;">
                    <b style="color:#1a73e8;">📍 {src['name']}</b><br>{safe_summary}
                </div>
                """)
        except Exception as e:
            print(f"跳过 {src['name']}: {e}")
            
    send_mail(results)
