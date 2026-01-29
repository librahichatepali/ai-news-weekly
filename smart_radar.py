import os
import time
import datetime
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

# 监控目标：针对性优化抓取规则
TARGET_SOURCES = [
    {"name": "游戏日报", "url": "https://www.gamelook.com.cn/category/mini-game", "selector": "h2 a"},
    {"name": "游戏陀螺", "url": "https://www.youxituoluo.com/tag/%E5%B0%8F%E6%B8%B8%E6%88%8F", "selector": "h2"},
    {"name": "DataEye", "url": "https://www.dataeye.com/report", "selector": "h3"},
    {"name": "小红书-她按开始键", "url": "https://www.xiaohongshu.com/user/profile/5df0a6990000000001000695", "selector": ".title"}
]

# --- 2. AI 精炼逻辑 ---
def ai_summarize(content):
    if not GEMINI_API_KEY: return "错误：未配置 API Key"
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    你是一个小游戏行业专家。以下是从行业网站抓取到的最新文章列表或动态。
    
    【任务】
    1. 识别出【2025年1月】至今发布的、关于“小游戏”题材、玩法或买量数据的干货。
    2. 忽略陈旧新闻和无关广告。
    3. 如果发现爆款题材（如修仙、副玩法、短剧+游戏等），请简要说明其核心吸引力。
    4. 若无符合条件的近30天内容，严格返回“无相关内容”。

    待处理数据：
    {content}
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"AI 总结失败: {str(e)}"

# --- 3. 邮件发送逻辑 ---
def send_final_mail(content_text):
    html_body = content_text.replace('\n', '<br>')
    html_content = f"""
    <div style="font-family: sans-serif; max-width: 650px; margin: auto; border: 1px solid #eee; padding: 25px; border-radius: 12px; background-color: #f4f7f9;">
        <h2 style="color: #1a73e8; border-bottom: 3px solid #1a73e8; padding-bottom: 12px; text-align: center;">🛡️ 小游戏·核心内参</h2>
        <div style="line-height: 1.7; color: #333; background: white; padding: 20px; border-radius: 8px;">
            {html_body}
        </div>
        <p style="font-size: 11px; color: #999; margin-top: 20px; text-align: center;">监控时效：近 30 天 | 状态：系统运行正常</p>
    </div>
    """
    msg = MIMEText(html_content, 'html', 'utf-8')
    msg['From'] = f"SmartRadar <{SENDER_EMAIL}>"
    msg['To'] = RECIPIENT_EMAIL
    msg['Subject'] = Header(f"🚨 小游戏精炼日报 - {time.strftime('%m-%d')}", 'utf-8')
    
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASS)
            server.sendmail(SENDER_EMAIL, [RECIPIENT_EMAIL], msg.as_string())
        print("✅ 邮件已发出")
    except Exception as e:
        print(f"❌ 发送失败: {e}")

# --- 4. 运行主函数 ---
def run_radar():
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0'}
    all_summaries = []

    for source in TARGET_SOURCES:
        try:
            print(f"🔍 正在深度扫描: {source['name']}...")
            resp = requests.get(source['url'], headers=headers, timeout=20)
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # 改进点：不再抓取全网页文字，而是只抓取标题类标签
            # 这样可以过滤掉侧边栏、导航栏的干扰，让 AI 直接看到文章列表
            elements = soup.select(source['selector'])
            found_titles = [el.get_text().strip() for el in elements if len(el.get_text().strip()) > 5]
            clean_text = "\n".join(found_titles[:15]) # 只取前15条最新标题
            
            if len(clean_text) < 20: continue # 抓取内容太少则跳过

            summary = ai_summarize(clean_text)
            if "无相关内容" not in summary:
                all_summaries.append(f"<b>【{source['name']} 最新发现】</b><br>{summary}<hr>")
        except Exception as e:
            print(f"❌ {source['name']} 扫描异常")

    if all_summaries:
        send_final_mail("\n".join(all_summaries))
    else:
        send_final_mail("系统报告：监控源已扫描，但未发现符合【2025年1月发布】且与【小游戏题材干货】相关的最新内容。")

if __name__ == "__main__":
    run_radar()
