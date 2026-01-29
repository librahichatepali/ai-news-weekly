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

# 监控目标：优化选择器以覆盖更多内容
TARGET_SOURCES = [
    {"name": "游戏日报", "url": "https://www.gamelook.com.cn/category/mini-game", "selector": "article, .post"},
    {"name": "游戏陀螺", "url": "https://www.youxituoluo.com/tag/%E5%B0%8F%E6%B8%B8%E6%88%8F", "selector": ".news-list, article"},
    {"name": "小红书-她按开始键", "url": "https://www.xiaohongshu.com/user/profile/5df0a6990000000001000695", "selector": ".note-item, .title"}
]

# --- 2. AI 精炼逻辑 ---
def ai_summarize(content):
    if not GEMINI_API_KEY: return "错误：未配置 API Key"
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # 强化 Prompt：明确要求即便只有标题也要进行趋势分析
    prompt = f"""
    你是一个小游戏行业专家。以下是最新抓取到的行业动态片段。
    
    【核心要求】
    1. 重点提取：2025年1月至今的爆款题材（如修仙、模拟经营、副玩法等）、买量成本变化、新玩法。
    2. 即使只有文章标题，也请根据标题预测当前的行业热点。
    3. 若内容包含具体数值（如消耗过亿、ROI等），务必加粗显示。
    4. 只有在内容完全不相关时才返回“无相关内容”。

    待处理数据：
    {content[:8000]}
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
    <div style="font-family: sans-serif; max-width: 650px; margin: auto; border: 1px solid #ddd; padding: 25px; border-radius: 12px; background-color: #ffffff;">
        <h2 style="color: #1a73e8; border-bottom: 3px solid #1a73e8; padding-bottom: 12px; text-align: center;">🚀 小游戏·实战内参</h2>
        <div style="line-height: 1.7; color: #333; padding: 10px;">
            {html_body}
        </div>
        <p style="font-size: 11px; color: #999; margin-top: 20px; text-align: center; border-top: 1px solid #eee; padding-top: 10px;">
            监控时间：{datetime.date.today()} | 状态：AI 深度扫描已完成
        </p>
    </div>
    """
    msg = MIMEText(html_content, 'html', 'utf-8')
    msg['From'] = f"SmartRadar <{SENDER_EMAIL}>"
    msg['To'] = RECIPIENT_EMAIL
    msg['Subject'] = Header(f"🔥 小游戏爆款雷达 - {time.strftime('%m-%d')}", 'utf-8')
    
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASS)
            server.sendmail(SENDER_EMAIL, [RECIPIENT_EMAIL], msg.as_string())
        print("✅ 邮件已送达")
    except Exception as e:
        print(f"❌ 发送失败: {e}")

# --- 4. 运行主函数 ---
def run_radar():
    print("🔍 正在启动全网深度扫描...")
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0'}
    all_summaries = []

    for source in TARGET_SOURCES:
        try:
            resp = requests.get(source['url'], headers=headers, timeout=20)
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # 改进：抓取更大范围的文本块以获取更多上下文
            content_blocks = soup.select(source['selector'])
            combined_text = "\n".join([b.get_text(separator=' ', strip=True) for b in content_blocks[:10]])
            
            if len(combined_text) < 50:
                # 备选方案：如果选择器失效，尝试抓取前 2000 个字符
                combined_text = soup.get_text(separator=' ', strip=True)[:2000]

            summary = ai_summarize(combined_text)
            if "无相关内容" not in summary:
                all_summaries.append(f"<b>📍 来源：{source['name']}</b><br>{summary}<br>")
        except Exception as e:
            print(f"❌ {source['name']} 扫描异常: {e}")

    if all_summaries:
        send_final_mail("\n".join(all_summaries))
    else:
        # 即使没发现，也发一封确认邮件
        send_final_mail("今日暂无题材爆发，建议关注 DataEye 榜单。")

if __name__ == "__main__":
    run_radar()
