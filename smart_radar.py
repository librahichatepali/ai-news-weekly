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

# 针对性选择容易产出“小游戏/H5”内容的源
TARGET_SOURCES = [
    {"name": "Pocket Gamer (移动游戏)", "url": "https://www.pocketgamer.biz/feed/"},
    {"name": "MobileGamer.biz", "url": "https://mobilegamer.biz/feed/"},
    {"name": "GameRefinery", "url": "https://www.gamerefinery.com/feed/"}
]

# --- 2. 纯搬运型 AI 函数：锁定小游戏 + 4条信息 ---
def ai_summarize(content, source_name):
    if not GEMINI_API_KEY: return ""
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    # 彻底简化：不再进行“是否有价值”的判定
    # 强制要求提取小游戏相关并凑足4条
    prompt = f"""
    任务：你是专业游戏翻译。请从以下 {source_name} 的新闻中提取【4条】与“小游戏”、“移动游戏”或“排行榜”相关的动态。
    
    要求：
    1. 必须翻译成中文。
    2. 禁止回答“无深度资讯”或“无相关内容”。
    3. 如果小游戏内容不足4条，请用该媒体最新的其他重要动态补齐，确保产出4条。
    
    待处理内容：
    {content}
    """
    
    try:
        response = requests.post(api_url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=60)
        res_json = response.json()
        if "candidates" in res_json:
            return res_json["candidates"][0]["content"]["parts"][0]["text"].strip()
        return ""
    except:
        return ""

# --- 3. 稳健发送：修复变量并确保渲染 ---
def send_mail(content_list, backup_titles):
    ai_output = "".join(content_list).strip()
    
    # 确保变量名正确，防止 image_9ab91c 中的 NameError 再次发生
    if not ai_output:
        list_str = "".join([f"<li>{t}</li>" for t in backup_titles])
        main_body = f"""
        <div style="background:#fff3cd; padding:15px; border-radius:5px;">
            ⚠️ 抓取测试中：AI 接口未返回，以下为直接抓取的原始标题：
            <ul>{list_str}</ul>
        </div>
        """
    else:
        main_body = ai_output

    html_layout = f"""
    <div style="font-family:sans-serif; max-width:600px; margin:auto; border:1px solid #eee; padding:20px; border-radius:10px;">
        <h2 style="color:#1a73e8; border-bottom:2px solid #1a73e8; padding-bottom:10px;">🧪 小游戏内容·压力测试</h2>
        <div style="line-height:1.7;">{main_body}</div>
        <hr style="border:0; border-top:1px solid #eee; margin:20px 0;">
        <div style="font-size:12px; color:#aaa; text-align:center;">
            测试模式: 锁定小游戏+强制4条 | 时间: {time.strftime("%Y-%m-%d %H:%M")}
        </div>
    </div>
    """
    
    msg = MIMEText(html_layout, 'html', 'utf-8')
    msg['From'] = f"SmartRadar <{SENDER_EMAIL}>"
    msg['To'] = RECIPIENT_EMAIL
    msg['Subject'] = Header(f"【测试】小游戏专题追踪 - {time.strftime('%m-%d')}", 'utf-8')
    
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASS)
            server.sendmail(SENDER_EMAIL, [RECIPIENT_EMAIL], msg.as_string())
        print("✅ 测试报告已发出")
    except Exception as e:
        print(f"❌ 发送失败: {e}")

# --- 4. 主运行逻辑 ---
if __name__ == "__main__":
    final_results = []
    all_captured_titles = [] # 明确修复变量名
    
    for src in TARGET_SOURCES:
        try:
            print(f"📡 正在扫描: {src['name']}...")
            r = requests.get(src['url'], timeout=20)
            soup = BeautifulSoup(r.text, 'xml')
            items = soup.find_all('item')[:10] # 扩大抓取范围，确保有足够素材
            
            raw_text = ""
            for it in items:
                title = it.find('title').text
                all_captured_titles.append(f"[{src['name']}] {title}")
                raw_text += f"- {title}\n"
            
            if raw_text:
                summary = ai_summarize(raw_text, src['name'])
                if summary:
                    safe_summary = summary.replace('\n', '<br>')
                    section = f"""
                    <div style="margin-bottom:15px; padding:10px; background:#f8f9fa; border-left:4px solid #1a73e8;">
                        <b>📍 来自: {src['name']}</b><br>{safe_summary}
                    </div>
                    """
                    final_results.append(section)
        except Exception as e:
            print(f"⚠️ {src['name']} 异常: {e}")
            
    send_mail(final_results, all_captured_titles)
