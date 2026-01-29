# --- 修正后的 AI 精炼函数 ---
def ai_summarize(content):
    if not GEMINI_API_KEY:
        return "错误：未配置 API Key"
    
    genai.configure(api_key=GEMINI_API_KEY)
    
    # 核心修正：将 gemini-pro 改为更稳定的 gemini-1.5-flash
    # flash 模型速度更快，且对免费层级更友好
    model = genai.GenerativeModel('gemini-1.5-flash') 
    
    prompt = f"""
    你是一个资深的小游戏行业分析师。请阅读以下内容，提炼核心干货：
    1. 重点：题材亮点、核心玩法、买量数据、行业趋势。
    2. 剔除废话，如果无关则返回“无相关内容”。
    
    内容如下：
    {content[:5000]} 
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        # 捕获具体的错误并返回，方便我们调试
        return f"AI 总结失败，请检查模型名称或 API Key。错误详情: {str(e)}"

# --- 邮件正文生成的修正 ---
def send_final_mail(content_text):
    # 修复之前的 SyntaxError：不在 f-string 内部处理反斜杠
    safe_html_content = content_text.replace('\n', '<br>')
    
    html_content = f"""
    <div style="font-family: sans-serif; max-width: 600px; margin: auto; border: 1px solid #eee; padding: 20px; border-radius: 10px;">
        <h2 style="color: #1a73e8; border-bottom: 2px solid #1a73e8; padding-bottom: 10px;">💎 今日小游戏精华内参</h2>
        <div style="line-height: 1.6; color: #333;">
            {safe_html_content}
        </div>
        <p style="font-size: 11px; color: #999; margin-top: 30px; border-top: 1px dashed #ccc; padding-top: 10px;">
            注：本报告由 Gemini AI (1.5-flash) 自动生成。
        </p>
    </div>
    """
    # ... 其余发送邮件的逻辑保持不变 ...
