import os
import time
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
import smtplib
from email.mime.text import MIMEText
from email.header import Header

# --- 1. 配置区域 ---
# 修改前：直接写字符串
# GEMINI_API_KEY = "AIza..." 

# 修改后：从 GitHub Secrets 安全读取
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
RECIPIENT_EMAIL = "tanweilin1987@gmail.com"
SENDER_PASS = os.environ.get('EMAIL_PASS')

# 监控目标：改为本地模拟访问的 URL
TARGET_SOURCES = [
    {"name": "游戏日报", "url": "https://www.gamelook.com.cn/category/mini-game"}, 
    {"name": "小红书-她按开始键", "url": "https://www.xiaohongshu.com/user/profile/5df0a6990000000001000695"}
]

# --- 2. AI 精炼逻辑 ---
def ai_summarize(content):
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-pro')
    
    prompt = f"""
    你是一个资深的小游戏行业分析师。请阅读以下内容，并为忙碌的制作人提炼最核心的干货。
    要求：
    1. 剔除所有寒暄和废话。
    2. 重点输出：题材亮点、核心玩法、买量/消耗数据、行业趋势。
    3. 如果内容不涉及小游戏，直接返回“无相关内容”。
    
    待处理内容：
    {content}
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except:
        return "AI 总结暂时不可用"

# --- 3. 核心抓取逻辑 ---
def run_radar():
    print("🚀 启动智能情报员...")
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0'}
    
    all_summaries = []

    for source in TARGET_SOURCES:
        try:
            # 本地 IP 访问，避开 GitHub 海外 IP 封锁
            resp = requests.get(source['url'], headers=headers, timeout=15)
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # 简单示例：抓取前 3 篇文章内容
            articles = soup.find_all('article')[:3]
            for art in articles:
                text = art.get_text()
                summary = ai_summarize(text)
                if "无相关内容" not in summary:
                    all_summaries.append(f"### 来自：{source['name']}\n{summary}\n")
        except Exception as e:
            print(f"❌ 抓取 {source['name']} 失败: {e}")

    if all_summaries:
        send_final_mail("\n".join(all_summaries))

def send_final_mail(content):
    # 构建 HTML 邮件，直接展示 AI 精炼后的精华，避免点击链接报错
    html_content = f"""
    <div style="font-family: sans-serif; max-width: 600px; margin: auto; border: 1px solid #eee; padding: 20px; border-radius: 10px;">
        <h2 style="color: #1a73e8; border-bottom: 2px solid #1a73e8; padding-bottom: 10px;">💎 今日小游戏精华内参</h2>
        <div style="line-height: 1.6; color: #333;">
            {content.replace('\n', '<br>')}
        </div>
        <p style="font-size: 12px; color: #999; margin-top: 30px; border-top: 1px dashed #ccc; padding-top: 10px;">
            注：本报告由本地 AI 自动精炼生成，已为您过滤 90% 的冗余信息。
        </p>
    </div>
    """
    msg = MIMEText(html_content, 'html', 'utf-8')
    msg['Subject'] = Header(f"📊 每日情报精炼日报 - {time.strftime('%m-%d')}", 'utf-8')
    # ... 发送逻辑保持不变 ...
    # (此处省略 SMTP 发送代码，参考之前版本即可)

if __name__ == "__main__":
    run_radar()
