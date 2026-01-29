import os
import time
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

TARGET_SOURCES = [
    {"name": "游戏日报", "url": "https://www.gamelook.com.cn/category/mini-game"},
    {"name": "游戏陀螺", "url": "https://www.youxituoluo.com/tag/%E5%B0%8F%E6%B8%B8%E6%88%8F"},
    {"name": "小红书-她按开始键", "url": "https://www.xiaohongshu.com/user/profile/5df0a6990000000001000695"}
]

# --- 2. AI 逻辑 (强化总结能力) ---
def ai_summarize(content):
    if not GEMINI_API_KEY: return "❌ 未检测到 Key"
    try:
        # 强制使用 v1 稳定版接口
        genai.configure(api_key=GEMINI_API_KEY, transport='rest')
        model = genai.GenerativeModel(model_name='gemini-1.5-flash')
        
        # 优化 Prompt：让 AI 更加积极地总结，即使没有完全匹配的“干货”
        prompt = f"""
        你是一个资深小游戏分析师。请阅读以下网页内容，并完成以下任务：
        1. 找出所有关于“小游戏”或“移动游戏”的新闻标题。
        2. 提炼出当前行业关注的【题材】、【玩法】或【商业化趋势】。
        3. 如果内容较少，请基于现有标题对 2026年1月 的行业走向做简要推测。
        
        待分析内容：
        {content[:4500]}
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return "⚠️ AI 扫描提示: " + str(e)

# --- 3. 邮件发送逻辑 ---
def send_mail(content_list):
    full_body = "".join(content_list)
    
    # 如果列表为空，说明抓取彻底失败
    if not full_body.strip():
        full_body = "<p style='color:orange;'>系统报告：今日目标站点暂无新的小游戏相关动态，建议检查源链接是否有效。</p>"

    html_content = f"""
    <div style="font-family: 'Microsoft YaHei', sans-serif; max-width: 700px; margin: auto; border: 1px solid #e0e0e0; padding: 30px; border-radius: 15px; background-color: #ffffff;">
        <h2 style="color: #1a73e8; border-bottom: 4px solid #1a73e8; padding-bottom: 15px; text-align: center; letter-spacing: 2px;">🛡️ 小游戏·情报内参</h2>
        <div style="line-height: 1.8; color: #333; font-size: 15px;">
            {full_body}
        </div>
        <div style="font-size: 12px; color: #aaa; text-align: center; border-top: 1px solid #eee; margin-top: 30px; padding-top: 15px;">
            监控时间：{time.strftime('%Y-%m-%d %H:%M')} | 核心引擎：Gemini 1.5 Stable
        </div>
    </div>
    """
    msg = MIMEText(html_content, 'html', 'utf-8')
    msg['From'] = f"SmartRadar <{SENDER_EMAIL}>"
    msg['To'] = RECIPIENT_EMAIL
    msg['Subject'] = Header(f"📊 小游戏雷达报告 - {time.strftime('%m-%d')}", 'utf-8')
    
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASS)
            server.sendmail(SENDER_EMAIL, [RECIPIENT_EMAIL], msg.as_string())
        print("✅ 邮件已成功发送至：" + RECIPIENT_EMAIL)
    except Exception as e:
        print("❌ 邮件发送异常: " + str(e))

# --- 4. 执行流程 ---
if __name__ == "__main__":
    final_results = []
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    for source in TARGET_SOURCES:
        try:
            print(f"正在扫描: {source['name']}...")
            r = requests.get(source['url'], headers=headers, timeout=20)
            soup = BeautifulSoup(r.text, 'html.parser')
            
            # 强化文本提取：获取所有段落和标题内容
            text = soup.get_text(separator=' ', strip=True)
            
            summary = ai_summarize(text)
            
            # 只要 AI 返回了有效字数，就计入结果
            if len(summary) > 50:
                formatted_summary = summary.replace('\n', '<br>')
                final_results.append(f"""
                <div style="margin-bottom: 25px; padding: 15px; background-color: #f8f9fa; border-left: 5px solid #1a73e8;">
                    <b style="color: #1a73e8; font-size: 17px;">📍 来源：{source['name']}</b><br>
                    <div style="margin-top: 10px;">{formatted_summary}</div>
                </div>
                """)
        except Exception as e:
            print(f"抓取 {source['name']} 失败: {e}")

    send_mail(final_results)
