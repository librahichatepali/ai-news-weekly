# --- 修改后的 AI 逻辑：强制输出模式 ---
def ai_summarize(content, source_name):
    if not GEMINI_API_KEY: return "❌ 错误：未配置 Key"
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    # 调整策略：要求 AI 必须对所有标题进行中文翻译和分类，不再进行“价值过滤”
    prompt = f"""
    你是一个专业的游戏行业助手。请对来自 {source_name} 的最新新闻标题进行快速综述。
    任务：
    1. 将以下所有新闻标题翻译为中文。
    2. 按类型分类（如：市场动态、新游测试、厂商新闻）。
    3. 如果没有任何标题，才回复“今日暂无更新”。
    
    待处理列表：
    {content[:15000]}
    """
    
    try:
        response = requests.post(api_url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=60)
        res_json = response.json()
        if "candidates" in res_json:
            return res_json["candidates"][0]["content"]["parts"][0]["text"]
        return "今日暂无更新"
    except Exception:
        return "⚠️ AI 响应异常"

# --- 修改后的主逻辑：增加内容保底 ---
if __name__ == "__main__":
    results = []
    # 增加更多具有活力的源，确保“必有产出”
    TARGET_SOURCES = [
        {"name": "Pocket Gamer (移动端)", "url": "https://www.pocketgamer.biz/feed/"},
        {"name": "MobileGamer.biz (深度专栏)", "url": "https://mobilegamer.biz/feed/"},
        {"name": "GameRefinery (市场趋势)", "url": "https://www.gamerefinery.com/feed/"}
    ]
    # ... 其余逻辑保持 RSS 抓取不变 ...
