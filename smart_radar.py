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
    {"name": "小红书-她按开始键", "url": "https://www.xiaohongshu.com/user/profile/5df0a6990000000001000695"},
    {"name": "DataEye报告", "url": "https://www.dataeye.com/report"}
]

# --- 2. AI 核心引擎 ---
def ai_summarize(content):
    if not GEMINI_API_KEY: return "❌ 错误：未检测到 API Key"
    try:
        # 强制指定 v1 协议以解决 404 models not found 问题
        genai.configure(api_key=GEMINI_API_KEY, transport='rest')
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        你是一位资深游戏分析师。请从以下内容中提炼【近一个月内】的小游戏情报：
        - 重点分析 2026年1月 的新题材、玩法趋势或买量爆款。
        - 提炼 3 条具有实战价值的建议。
        
        待处理内容：
        {content[:4000]}
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"⚠️ AI 总结受阻：{str(e)}"

# --- 3. 邮件发送系统 ---
def send_mail(content_list):
    full_body = "".join(content_list)
    if not full_body.strip():
        full_body = "<p style='color:orange;'>今日扫描完成，但各监控源暂无近期更新的深度内容。</p>"

    html_content = f"""
    <div style="font-family: sans-serif; max-width: 700px; margin: auto; border: 1px solid #eee; padding: 25px; border-radius: 12px;">
        <h2 style="color: #1a73e8; border-bottom: 3px solid #1a73e8; padding-bottom: 10px; text-align: center;">
