import os
import time
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
import smtplib
from email.mime.text import MIMEText
from email.header import Header

# --- 1. 配置区域 (保持 Secret 变量名一致) ---
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
RECIPIENT_EMAIL = "tanweilin1987@gmail.com"
SENDER_EMAIL = os.environ.get('EMAIL_USER')
SENDER_PASS = os.environ.get('EMAIL_PASS')

# 监控源配置：增加 DataEye 作为深度报告补充
TARGET_SOURCES = [
    {"name": "游戏日报", "url": "https://www.gamelook.com.cn/category/mini-game"},
    {"name": "游戏陀螺", "url": "https://www.youxituoluo.com/tag/%E5%B0%8F%E6%B8%B8%E6%88%8F"},
    {"name": "小红书-她按开始键", "url": "https://www.xiaohongshu.com/user/profile/5df0a6990000000001000695"},
    {"name": "DataEye-报告", "url": "https://www.dataeye.com/report"}
]

# --- 2. AI 核心引擎 (深度修复 404 & 增强时效分析) ---
def ai_summarize(content):
    if not GEMINI_API_KEY: return "❌ 未检测到 Key"
    try:
        # 核心操作 1：强制指定 v1 协议，解决 v1beta 导致的 404 报错
        genai.configure(api_key=GEMINI_API_KEY, transport='rest')
        
        # 核心操作 2：使用更稳健的模型标识符
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # 核心操作 3：模糊日期指令，让 AI 替代代码进行日期筛选
        prompt = f"""
        你是一位资深游戏猎头和数据分析师。请从以下网页内容中挖掘【近一个月内】的小游戏行业价值信息：
        - 识别任何关于 2026年1月 的新题材、新玩法或买量爆款。
        - 提炼 3 条具有实战价值的行业趋势（如：ROI、题材组合、技术点）。
        - 剔除与小游戏无关的广告和过期信息。
        
        待分析内容：
        {content[:4500]}
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        # 核心操作 4：模型回退机制，确保必有产出
        try:
            model_backup = genai.GenerativeModel('gemini-pro')
            return model_backup.generate_content("提炼内容要点：" + content[:3000]).text
        except:
            return f"⚠️ AI 诊断提示：{str(e)}"

# --- 3. 邮件发送系统 ---
def send_mail(content_list):
    full_body = "".join(content_list)
    if not full_body.strip():
        full_body = "<p style='color:orange;'>系统报告：今日扫描完成，但目标源暂时没有抓取到具有价值的小游戏干货。建议检查链接有效性。</p>"

    html_content = f"""
    <div style="font-family: 'Microsoft YaHei', sans-serif; max-width: 750px; margin: auto; border: 1px solid #eef0f2; padding: 30px; border-radius: 16px; background-color: #ffffff; box-shadow: 0 4px 15px rgba(0,0,0,0.05);">
        <h2 style="color: #1a73e8; border-bottom: 4px solid #1a73e8; padding-bottom: 15px; text-align: center; font-size: 24px;">🛡️ 小游戏·深度情报雷达</h2>
        <div style="line-height: 1.8; color: #333; font-size: 15px;">
            {full_body}
        </div>
        <div style="font-size: 12px; color: #99aab5; text-align: center; border-top: 1px solid #eee; margin-top: 30px; padding-top: 20px;">
            监控时效：近 30 天 | 核心引擎：Gemini 1.5 Stable | 时间：{time.strftime('%Y-%m-%d %H:%M')}
        </div>
    </div>
    """
    msg = MIMEText(html_content, 'html', 'utf-8')
    msg['From'] = f"SmartRadar <{SENDER_EMAIL}>"
    msg['To'] = RECIPIENT_EMAIL
    msg['Subject'] = Header(f"📊 小游戏月度趋势 - 核心内参 - {time.strftime('%m-%d')}", 'utf-8')
    
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASS)
            server.sendmail(SENDER_EMAIL, [RECIPIENT_EMAIL], msg.as_string())
        print("✅ 报告发送成功")
    except Exception as e:
        print(f"❌ 邮件系统故障: {e}")

# --- 4. 自动化执行链路 ---
if __name__ == "__main__":
    final_results = []
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    
    for source in TARGET_SOURCES:
        try:
            print(f"正在深度扫描: {source['name']}...")
            r = requests.get(source['url'], headers=headers, timeout=25)
            soup = BeautifulSoup(r.text, 'html.parser')
            
            # 操作 5：全文抓取，不再对单篇文章日期做前置硬过滤
            raw_text = soup.get_text(separator=' ', strip=True)
            
            summary = ai_summarize(raw_text)
            
            # 只要 AI 返回了有效字符，就封装进邮件
            if len(summary) > 60:
                formatted_summary = summary.replace('\n', '<br>')
                final_results.append(f"""
                <div style="margin-bottom: 25px; padding: 20px; background-color: #f8faff; border-left: 6px solid #1a73e8; border-radius: 4px;">
                    <b style="color: #1a73e8; font-size: 18px;">📍 来源：{source['name']}</b><br>
                    <div style="margin-top: 12px; color: #444;">{formatted_summary}</div>
                </div>
                """)
        except Exception as e:
            print(f"⚠️ {source['name']} 扫描受阻: {e}")

    send_mail(final_results)
