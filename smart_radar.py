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

# 监控源（保持不变，确保抓取广度）
TARGET_SOURCES = [
    {"name": "Pocket Gamer", "url": "https://www.pocketgamer.biz/feed/"},
    {"name": "MobileGamer.biz", "url": "https://mobilegamer.biz/feed/"},
    {"name": "GameRefinery", "url": "https://www.gamerefinery.com/feed/"}
]

# --- 2. 强力抓取逻辑：强制 4 条，取消筛选 ---
def ai_summarize(content, source_name):
    if not GEMINI_API_KEY: return ""
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    # 调整后的 Prompt：不再挑剔，只管翻译并补齐 4 条
    prompt = f"""
    任务：你是游戏情报搬运工。请从以下 {source_name} 的新闻中提取【4条】关键动态。
    
    重点搜索词（如果发现请务必列出）：
    - 小游戏 (Mini-games / H5 / Instant Games)
    - 排行榜 / 热销 (Charts / Top Grossing / Ranking)
    - 市场大盘数据
    
    硬性要求：
    1. 必须输出 4 条信息，不要回答“无相关内容”或“无深度资讯”。
    2. 如果关于小游戏的内容不足 4 条，请用该源的其他最新新闻补足。
    3. 全部使用中文。
    
    待处理内容：
    {content}
    """
    
    try:
        response = requests.post(api_url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=60)
        res_json = response.json()
        if "candidates" in res_json:
            return res_json["candidates"][0]["content"]["parts"][0]["text"].strip()
        return ""
    except Exception as e:
        print(f"AI 接口异常: {e}")
        return ""

# --- 3. 邮件发送系统：彻底修复变量名报错 ---
def send_mail(content_list, backup_titles):
    ai_output = "".join(content_list).strip()
    
    # 修复 NameError，使用 backup_titles 作为保底
    if not ai_output:
        list_str = "".join([f"<li>{t}</li>" for t in backup_titles])
        main_body = f"""
        <div style="background:#fff3cd; padding:15px; border-radius:8px;">
            ⚠️ AI 接口未产出（可能由于网络原因），以下为系统直接抓取的原始标题：
            <ul>{list_str}</ul>
        </div>
        """
    else:
        main_body = ai_output

    html_layout = f"""
    <div style="font-family:sans-serif; max-width:650px; margin:auto; border:1px solid #eee; padding:25px; border-radius:15px; background:#fff;">
        <h2 style="color:#1a73e8; text-align:center; border-bottom:2px solid #1a73e8; padding-bottom:10px;">🧪 情报获取能力测试</h2>
        <div style="line-height:1.8; color:#333;">{main_body}</div>
        <div style="font-size:12px; color:#aaa; text-align:center; margin-top:30px; border-top:1px solid #f0f0f0; padding-top:15px;">
            监控模式: 小游戏/热销/强制4条 | 时间: {time.strftime("%Y-%m-%d %H:%M")}
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
        print("✅ 邮件已发送")
    except Exception as e:
        print(f"❌ 发送失败: {e}")

# --- 4. 运行主逻辑 ---
if __name__ == "__main__":
    final_results = []
    all_captured_titles = [] # 明确定义，修复 NameError
    
    for src in TARGET_SOURCES:
        try:
            print(f"📡 抓取源: {src['name']}...")
            r = requests.get(src['url'], timeout=20)
            soup = BeautifulSoup(r.text, 'xml')
            items = soup.find_all('item')[:10] # 扩大采样范围
            
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
                    <div style="margin-bottom:20px; padding:15px; background:#f8f9fa; border-left:5px solid #1a73e8;">
                        <b style="color:#1a73e8;">📍 {src['name']} 最新动态：</b><br>
                        <div style="margin-top:8px; font-size:14px;">{safe_summary}</div>
                    </div>
                    """
                    final_results.append(section)
        except Exception as e:
            print(f"⚠️ {src['name']} 异常: {e}")
            
    send_mail(final_results, all_captured_titles)
