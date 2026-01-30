import os
import time
import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.header import Header

# --- 1. 基础配置 ---
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
RECIPIENT_EMAIL = "tanweilin1987@gmail.com"
SENDER_EMAIL = os.environ.get('EMAIL_USER')
SENDER_PASS = os.environ.get('EMAIL_PASS')

# 选用目前测试最稳、内容质量最高的源
TARGET_SOURCES = [
    {"name": "GameLook", "url": "http://www.gamelook.com.cn/"},
    {"name": "Pocket Gamer", "url": "https://www.pocketgamer.biz/"}
]

# --- 2. 增强型 AI 翻译官：纯净翻译模式 ---
def ai_summarize(content, source_name):
    if not GEMINI_API_KEY: return None
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    # 采用去敏感化的指令，仅要求翻译，降低 AI 拦截概率
    prompt = f"你是专业的游戏行业翻译。请将以下来自 {source_name} 的标题翻译成简练的中文，每条一行。严禁评价内容：\n{content}"
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ],
        "generationConfig": {
            "temperature": 0.1,  # 降低随机性，确保输出稳定
            "maxOutputTokens": 1000
        }
    }
    
    try:
        response = requests.post(api_url, json=payload, timeout=30)
        res_json = response.json()
        
        # 稳健提取 API 响应，防止 'candidates' 键缺失报错
        if "candidates" in res_json and res_json["candidates"][0].get("content"):
            return res_json["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        print(f"AI 接口异常: {e}")
    return None

# --- 3. 稳健邮件发送：带 HTML 格式优化 ---
def send_mail(sections):
    # 如果所有源都失败，至少发送一个状态通知
    main_body = "".join(sections) if sections else "<p>今日暂无新情报获取，请检查网络连接。</p>"
    
    html_layout = f"""
    <div style="font-family:sans-serif; max-width:650px; margin:auto; border:1px solid #e0e0e0; padding:25px; border-radius:12px; color:#333;">
        <h2 style="color:#1a73e8; border-bottom:2px solid #1a73e8; padding-bottom:10px; margin-top:0;">🚀 每日情报 · 游戏市场雷达</h2>
        {main_body}
        <div style="margin-top:30px; padding-top:15px; border-top:1px solid #eee; font-size:12px; color:#888; text-align:center;">
            引擎: Gemini 1.5 Flash | 模式: 自动翻译+备份 | 时间: {time.strftime("%Y-%m-%d %H:%M")}
        </div>
    </div>
    """
    
    msg = MIMEText(html_layout, 'html', 'utf-8')
    msg['From'] = f"SmartRadar <{SENDER_EMAIL}>"
    msg['To'] = RECIPIENT_EMAIL
    msg['Subject'] = Header(f"🎮 市场情报简报 - {time.strftime('%m-%d')}", 'utf-8')
    
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASS)
            server.sendmail(SENDER_EMAIL, [RECIPIENT_EMAIL], msg.as_string())
        print("✅ 邮件报告已发送")
    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")

# --- 4. 主运行程序：绕过所有历史陷阱 ---
if __name__ == "__main__":
    final_sections = []
    # 模拟真实浏览器，减少被网站屏蔽的风险
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0'}

    for src in TARGET_SOURCES:
        try:
            print(f"📡 正在探测: {src['name']}...")
            r = requests.get(src['url'], headers=headers, timeout=25)
            
            if r.status_code != 200:
                print(f"⚠️ {src['name']} 访问受限 (Code {r.status_code})")
                continue
            
            # 使用内置解析器，不依赖外部 LXML
            soup = BeautifulSoup(r.text, 'html.parser')
            # 智能提取新闻标题：过滤掉过短的干扰文本
            raw_titles = [t.text.strip() for t in soup.find_all(['h2', 'h3'])[:15] if len(t.text.strip()) > 8]
            
            if raw_titles:
                content_to_translate = "\n".join(raw_titles)
                summary = ai_summarize(content_to_translate, src['name'])
                
                # 如果 AI 翻译成功，使用翻译；否则自动降级到原始标题列表
                if summary:
                    # 将换行符转为 HTML 换行，并移出 f-string 以修复语法报错
                    display_text = summary.replace('\n', '<br>')
                else:
                    display_text = "<span style='color:#f39c12;'>AI 响应超时，展示原始列表：</span><br>" + "<br>".join(raw_titles)
                
                # 构建 HTML 区块
                section_html = "<h3>📍 来自: " + src['name'] + "</h3>"
                section_html += "<div style='background:#f9f9f9; padding:15px; border-radius:8px; line-height:1.6;'>" + display_text + "</div>"
                final_sections.append(section_html)
                
        except Exception as e:
            print(f"❌ 处理 {src['name']} 时出错: {e}")

    send_mail(final_sections)
