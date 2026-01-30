import os
import time
import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.header import Header

# --- 1. 配置区域 ---
# 请确保在 GitHub Secrets 中配置了以下变量
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
RECIPIENT_EMAIL = "tanweilin1987@gmail.com"
SENDER_EMAIL = os.environ.get('EMAIL_USER')
SENDER_PASS = os.environ.get('EMAIL_PASS')

# 选取的 RSS 源：这些源更新频率高，信噪比极佳
TARGET_SOURCES = [
    {"name": "Pocket Gamer (移动游戏)", "url": "https://www.pocketgamer.biz/feed/"},
    {"name": "MobileGamer.biz (行业专栏)", "url": "https://mobilegamer.biz/feed/"},
    {"name": "GameRefinery (市场分析)", "url": "https://www.gamerefinery.com/feed/"}
]

# --- 2. AI 核心：强力综述模式 ---
def ai_summarize(content, source_name):
    if not GEMINI_API_KEY: return "❌ 错误：未配置 API Key"
    
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    # 修改后的 Prompt：不再挑食，强制翻译并综述所有内容
    prompt = f"""
    你是一位资深移动游戏行业情报分析师。
    任务：请对来自 {source_name} 的最新新闻列表进行中文综述。
    要求：
    1. 翻译所有标题，并提取其核心内容。
    2. 按类别（如：新游测试、厂商动态、市场趋势）进行整理。
    3. 语言风格要专业、干练。
    4. 如果文本为空，才回复“今日暂无更新”。

    待处理数据：
    {content[:15000]}
    """
    
    try:
        response = requests.post(api_url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=60)
        res_json = response.json()
        if "candidates" in res_json:
            return res_json["candidates"][0]["content"]["parts"][0]["text"]
        return "今日暂无更新"
    except Exception as e:
        return f"⚠️ AI 处理异常: {str(e)}"

# --- 3. 邮件发送系统 ---
def send_mail(content_list):
    combined_body = "".join(content_list)
    
    # 状态逻辑：如果没有任何内容，发出状态存活报告
    status_msg = ""
    if not combined_body.strip():
        status_msg = """
        <div style="padding:15px; border:1px dashed #ffa500; color:#856404; background:#fff3cd; border-radius:10px; margin-bottom:20px;">
            📡 <b>系统存活报告：</b> RSS 链路解析正常，但 AI 判定今日源站暂无新增内容。
        </div>
        """

    # 严谨构建 HTML 模板，避免反斜杠语法错误
    html_layout = f"""
    <div style="font-family: 'Microsoft YaHei', sans-serif; max-width: 700px; margin: auto; border: 1px solid #e0e0e0; padding: 30px; border-radius: 12px; background-color: #ffffff;">
        <h2 style="color: #1a73e8; text-align: center; border-bottom: 3px solid #1a73e8; padding-bottom: 10px;">📊 全球游戏雷达 - 情报汇总</h2>
        {status_msg}
        <div style="line-height: 1.8; color: #333333;">
            {combined_body}
        </div>
        <div style="font-size: 12px; color: #aaaaaa; text-align: center; margin-top: 40px; border-top: 1px solid #eeeeee; padding-top: 20px;">
            数据源: RSS Feed | 引擎: Gemini 1.5 Flash | 时间: {time.strftime("%Y-%m-%d %H:%M")}
        </div>
    </div>
    """
    
    msg = MIMEText(html_layout, 'html', 'utf-8')
    msg['From'] = f"SmartRadar <{SENDER_EMAIL}>"
    msg['To'] = RECIPIENT_EMAIL
    msg['Subject'] = Header(f"🎮 游戏趋势动态报告 - {time.strftime('%m/%d')}", 'utf-8')
    
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASS)
            server.sendmail(SENDER_EMAIL, [RECIPIENT_EMAIL], msg.as_string())
        print("✅ 邮件已发出")
    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")

# --- 4. 运行主逻辑 ---
if __name__ == "__main__":
    results = []
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    for src in TARGET_SOURCES:
        try:
            print(f"📡 正在拉取 RSS: {src['name']}...")
            r = requests.get(src['url'], headers=headers, timeout=25)
            # RSS 是 XML 格式，不需要处理复杂的 HTML 降噪
            soup = BeautifulSoup(r.text, 'xml')
            items = soup.find_all('item')[:10] # 每次只抓取最新的 10 条
            
            feed_text = ""
            for item in items:
                title = item.find('title').get_text() if item.find('title') else ""
                description = item.find('description').get_text() if item.find('description') else ""
                feed_text += f"【标题】: {title}\n【摘要】: {description[:200]}\n\n"
            
            if len(feed_text) > 50:
                summary = ai_summarize(feed_text, src['name'])
                if "今日暂无更新" not in summary:
                    # 在此处处理换行符，避免在 f-string {} 中处理导致的语法错误
                    clean_summary = summary.replace('\n', '<br>')
                    section = f"""
                    <div style="margin-bottom: 25px; padding: 15px; border-left: 4px solid #1a73e8; background-color: #f8f9fa;">
                        <b style="color: #1a73e8; font-size: 16px;">📍 来源: {src['name']}</b><br>
                        <div style="margin-top: 10px; font-size: 14px;">{clean_summary}</div>
                    </div>
                    """
                    results.append(section)
            else:
                print(f"⚠️ {src['name']} 未获取到有效条目")
                
        except Exception as e:
            print(f"❌ 处理 {src['name']} 时出错: {e}")
            
    send_mail(results)
