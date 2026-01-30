# --- 1. 增强 AI 引擎的“容错输出”能力 ---
def ai_summarize(content, source_name):
    if not GEMINI_API_KEY: return "❌ 错误：未配置 Key"
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    # 优化 Prompt：明确告知网页可能存在的噪音，并要求即便只有标题也要提取
    prompt = f"""
    你是一位专业的移动游戏情报分析师。下面是来自 {source_name} 网站的最新原始网页文本。
    
    分析目标：
    - 忽略所有“Cookie Policy”、“Privacy”、“Sign up”等干扰项。
    - 寻找包含游戏名称、公司动作、市场数据的行业动态标题。
    - 哪怕只有一条关键标题，也请用中文列出。
    - 绝不要返回任何 HTML 标签。如果真的没有新动态，请统一回复“今日暂无重大更新”。
    
    待处理文本：
    {content[:15000]}
    """
    # (保持原有的 requests 发送逻辑...)

# --- 2. 优化抓取：引入“内容密度”过滤 ---
if __name__ == "__main__":
    results = []
    # (保持 headers 配置...)
    
    for src in TARGET_SOURCES:
        try:
            r = requests.get(src['url'], headers=headers, timeout=30)
            # 使用 apparent_encoding 自动识别编码，防止乱码干扰 AI
            r.encoding = r.apparent_encoding 
            
            soup = BeautifulSoup(r.text, 'html.parser')
            
            # 强化清洗：增加对 iframe, noscript 和 data-analytics 区域的删除
            for noise in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe', 'noscript']):
                noise.decompose()
            
            # 进阶技巧：只提取 <body> 标签内的文字，过滤掉外层的元数据
            body_content = soup.find('body')
            clean_text = body_content.get_text(separator=' ', strip=True) if body_content else soup.get_text(separator=' ', strip=True)
            
            summary = ai_summarize(clean_text, src['name'])
            
            # 只要不是完全报错且不是“暂无更新”，就记入结果
            if "今日暂无重大更新" not in summary and len(summary) > 20: # 降低门槛至 20 字符
                safe_summary = summary.replace('\n', '<br>')
                # (保持 HTML 生成逻辑...)
