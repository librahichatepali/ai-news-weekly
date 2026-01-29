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

# 监控目标：已扩充核心源
TARGET_SOURCES = [
    {"name": "游戏日报-小游戏", "url": "https://www.gamelook.com.cn/category/mini-game"},
    {"name": "游戏陀螺-情报", "url": "https://www.youxituoluo.com/tag/小游戏"},
    {"name": "DataEye-行业观察", "url": "https://www.dataeye.com/report"},
    {"name": "小红书-她按开始键", "url": "https://www.xiaohongshu.com/user/profile/5df0a6990000000001000695"}
]

# --- 2. AI 精炼逻辑 ---
def ai_summarize(content):
    if not GEMINI_API_KEY:
        return "错误：未配置 API Key"
    
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash') # 使用更稳定的版本
    
    # 设定精炼指令：强调 1 个月内的时间敏感度
    prompt = f"""
    你是一个资深的小游戏行业分析师。请阅读以下内容，并提炼核心干货。
    
    【核心任务】
    1. 仅关注并提炼【近1个月内】(即2024年12月至今) 的题材亮点、核心玩法、买量数据、行业趋势。
    2. 如果内容属于陈旧信息或与小游戏无关，请直接返回“无相关内容”。
    3. 重点解析：哪些题材正在爆发？哪些买量手法值得借鉴？
    
    待处理内容：
    {content[:6000]} 
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"AI 总结失败: {str(e)}"

# --- 3. 邮件发送逻辑 ---
def send_final_mail(content_text):
    html_body = content_text.replace('\n', '<br>') # 避免 f-string 语法错误
    
    html_content = f"""
    <div style="font-family: sans-serif; max-width: 650px; margin: auto; border: 1px solid #eee; padding: 25px; border-radius: 12px; background-color: #f9f9f9;">
        <h2 style="color: #1a73e8; border-bottom: 3px solid #1a73e8; padding-bottom: 12px; text-align: center;">🛡️ 小游戏·近30日情报精炼</h2>
        <div style="line-height: 1.7; color: #444; background: white; padding: 20px; border-radius: 8px; border: 1px solid #ddd;">
            {html_body}
        </div>
        <p style="font-size: 12px; color: #888; margin-top: 25px; text-align: center;">
            监控时效：近 30 天 | 来源：游戏日报/陀螺/DataEye/小红书
        </p>
    </div>
    """
    msg = MIMEText(html_content, 'html', 'utf-8')
    msg['From'] = f"SmartRadar <{SENDER_EMAIL}>"
    msg['To'] = RECIPIENT_EMAIL
    msg['Subject'] = Header(f"🚨 小游戏月度趋势雷达 - {time.strftime('%m-%d')}", 'utf-8')
    
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASS)
            server.sendmail(SENDER_EMAIL, [RECIPIENT_EMAIL], msg.as_string())
        print("✅ 情报报告已送达")
    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")

# --- 4. 运行主函数 ---
def run_radar():
    print(f"🚀 启动智能情报员 (当前日期: {datetime.date.today()})...")
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0'}
    all_summaries = []

    for source in TARGET_SOURCES:
        try:
            print(f"正在扫描: {source['name']}...")
            resp = requests.get(source['url'], headers=headers, timeout=20)
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # 获取网页文本内容
            raw_text = soup.get_text()
            
            # 交给 AI 进行时间过滤与精炼
            summary = ai_summarize(raw_text)
            
            if "无相关内容" not in summary and "总结失败" not in summary:
                all_summaries.append(f"<b>【{source['name']}】</b><br>{summary}<hr>")
        except Exception as e:
            print(f"❌ 扫描 {source['name']} 失败: {e}")

    if all_summaries:
        send_final_mail("\n".join(all_summaries))
    else:
        print("今日未发现近1个月内的符合题材")
        send_final_mail("系统运行报告：今日扫描完成，监控源中未发现近 1 个月内更新且符合条件的【小游戏题材】内容。")

if __name__ == "__main__":
    run_radar()
