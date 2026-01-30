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
    {"name": "Pocket Gamer News", "url": "https://www.pocketgamer.biz/news/"},
    {"name": "GameRefinery Blog", "url": "https://www.gamerefinery.com/blog/"},
    {"name": "MobileGamer.biz", "url": "https://mobilegamer.biz/news/"}
]

# --- 2. AI 引擎：增强容错与提取精度 ---
def ai_summarize(content, source_name):
    if not GEMINI_API_KEY: return "❌ 错误：未配置 Key"
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    # 优化 Prompt：允许 AI 提取单条简短动态，降低“无更新”的误判率
    prompt = f"""
    你是一位专业的游戏行业分析师。请从 {source_name} 的网页文本中提取今日核心动态。
    要求：
    - 忽略：隐私条款、登录入口、侧边栏广告、作者信息。
    - 重点：提取新游上线、厂商收购、重大财报、市场数据。
    - 哪怕只有一条关键标题，也请用中文列出。
    - 如果确定没有新动态，请仅回复：今日暂无重大更新。
    
    文本内容：
    {content[:13000]}
    """
    
    try:
        response = requests.post(api_url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=60)
        res_json = response.json()
        if "candidates" in res_json:
            return res_json["candidates"][0]["content"]["parts"][0]["text"]
        return "今日暂无重大更新"
    except Exception as e:
        return f"⚠️ API 调用失败: {str(e)}"

# --- 3. 邮件系统：彻底闭合结构，防止脚本崩溃 ---
def send_mail(content_list):
    combined_body = "".join(content_list)
    
    # 状态透明化：如果内容为空，显示状态简报
    if not combined_body.strip():
        combined_body = "<p style='color:#666;'>📡 今日各源暂无深度更新，探测器运行正常。</p>"

    html_layout = f"""
    <div style="font-family:sans-serif;max-width:700px;margin:auto;border:1px solid #ddd;padding:30px;border-radius:15px;">
        <h2 style="color:#1a73e8;text-align:center;border-bottom:4px solid #1a73e8;padding-bottom:12px;">🌍 全球游戏动态·探测报告</h2>
        <div style="line-height:1.7;color:#333;">{combined_body}</div>
        <div style="font-size:12px;color:#999;text-align:center;margin-top:40px;border-top:1px solid #eee;padding-top:20px;">
            验证状态：列表页深度清洗 | 引擎：Gemini 1.5 Flash | 时间：{time.strftime("%Y-%m-%d %H:%M")}
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
        print("✅ 报告已送达")
    except Exception as e:
        print(f"❌ 发送失败: {e}")

# --- 4. 强力抓取逻辑 ---
if __name__ == "__main__":
    results = []
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    for src in TARGET_SOURCES:
        try:
            print(f"正在扫描: {src['name']}...")
            r = requests.get(src['url'], headers=headers, timeout=25)
            r.encoding = r.apparent_encoding # 自动纠正编码，防止乱码干扰 AI
            soup = BeautifulSoup(r.text, 'html.parser')
            
            # 精准降噪：物理剔除所有交互和非新闻区域
            for noise in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe', 'noscript', 'form']):
                noise.decompose()
            
            clean_text = soup.get_text(separator=' ', strip=True)
            summary = ai_summarize(clean_text, src['name'])
            
            # 只要不是完全没有实质内容的“无更新”回复，就记入结果
            if "今日暂无重大更新" not in summary and len(summary) > 25:
                # 处理换行以适配邮件 HTML
                safe_summary = summary.replace('\n', '<br>')
                section = f"""
                <div style="margin-bottom:25px;padding:20px;background:#f9f9f9;border-left:5px solid #1a73e8;">
                    <b style="color:#1a73e8;font-size:16px;">📍 来源：{src['name']}</b><br>
                    <div style="margin-top:10px;font-size:14px;color:#444;">{safe_summary}</div>
                </div>
                """
                results.append(section)
        except Exception as e:
            print(f"跳过 {src['name']}: {e}")
            
    send_mail(results)
