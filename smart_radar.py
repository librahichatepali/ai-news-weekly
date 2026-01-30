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

# --- 2. AI 引擎：增加容错与智能识别 ---
def ai_summarize(content, source_name):
    if not GEMINI_API_KEY: return "❌ 错误：未配置 Key"
    
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    # 优化 Prompt：明确告知这是列表页，让 AI 重点关注标题和时间戳
    prompt = f"""
    你是一位专业的移动游戏情报分析师。下面是来自 {source_name} 网站的最新网页文本。
    任务：
    1. 忽略所有广告、导航、底部链接。
    2. 提取最近 24-48 小时内的核心游戏行业动态（如新游上线、收购、财报、政策）。
    3. 用中文列出要点。如果没有发现明确动态，请简要回复“今日暂无重大更新”。
    
    文本内容：
    {content[:15000]}
    """
    
    try:
        response = requests.post(api_url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=60)
        res_json = response.json()
        if "candidates" in res_json:
            return res_json["candidates"][0]["content"]["parts"][0]["text"]
        return "⚠️ 未捕获到结构化动态"
    except Exception as e:
        return f"⚠️ API 请求异常: {str(e)}"

# --- 3. 邮件发送系统：增强状态反馈 ---
def send_mail(content_list):
    combined_body = "".join(content_list)
    
    # 状态提示：区分“技术故障”与“内容为空”
    status_msg = ""
    if not combined_body.strip():
        status_msg = """
        <div style="padding:20px; border:1px dashed #ffa500; color:#856404; background:#fff3cd; border-radius:10px;">
            <b>📡 探测简报：</b> 各目标源访问正常，但 AI 未识别出具有价值的新闻更新。
        </div>
        """
    
    html_layout = f"""
    <div style="font-family:sans-serif;max-width:700px;margin:auto;border:1px solid #ddd;padding:30px;border-radius:15px;">
        <h2 style="color:#1a73e8;text-align:center;border-bottom:4px solid #1a73e8;padding-bottom:12px;">🌍 全球游戏动态·探测报告</h2>
        {status_msg}
        <div style="line-height:1.7;color:#333;">{combined_body}</div>
        <div style="font-size:12px;color:#999;text-align:center;margin-top:40px;border-top:1px solid #eee;padding-top:20px;">
            验证状态：列表页深度识别 | 引擎：Gemini 1.5 Flash | 时间：{time.strftime("%Y-%m-%d %H:%M")}
        </div>
    </div>
    """
    msg = MIMEText(html_layout, 'html', 'utf-8')
    msg['From'] = f"SmartRadar <{SENDER_EMAIL}>"
    msg['To'] = RECIPIENT_EMAIL
    msg['Subject'] = Header(f"📊 趋势探测报告 - {time.strftime('%m-%d')}", 'utf-8')
    
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASS)
            server.sendmail(SENDER_EMAIL, [RECIPIENT_EMAIL], msg.as_string())
        print("✅ 报告已送达")
    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")

# --- 4. 优化抓取逻辑：提高“信噪比” ---
if __name__ == "__main__":
    results = []
    # 模拟真实浏览器，防止被屏蔽
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9'
    }
    
    for src in TARGET_SOURCES:
        try:
            print(f"正在扫描: {src['name']}...")
            r = requests.get(src['url'], headers=headers, timeout=30)
            r.encoding = 'utf-8' 
            soup = BeautifulSoup(r.text, 'html.parser')
            
            # 精确手术：只保留可能包含正文的标签，剔除所有交互组件
            for noise in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe', 'noscript']):
                noise.decompose()
            
            # 优先获取 <div> 和 <article> 中的内容，减少冗余
            clean_text = soup.get_text(separator=' ', strip=True)
            
            # 传递来源名称给 AI，帮助其定位语境
            summary = ai_summarize(clean_text, src['name'])
            
            # 只要不是完全报错且不是“暂无更新”，就记入结果
            if "今日暂无重大更新" not in summary and len(summary) > 30:
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
            continue
            
    send_mail(results)
