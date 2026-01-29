import smtplib
import os
import time
from email.mime.text import MIMEText
from email.header import Header

def send_commander_report():
    # 彻底解决 404 和 未知错误，改用深度链接协议
    html = """
    <div style="max-width: 600px; margin: 0 auto; font-family: 'Microsoft YaHei', sans-serif; background: #f9f9f9; border-radius: 16px; overflow: hidden; border: 1px solid #eee;">
        <div style="background: linear-gradient(135deg, #6200EE 0%, #3700B3 100%); color: white; padding: 30px 20px; text-align: center;">
            <h1 style="margin: 0; font-size: 22px;">🎮 小游戏题材监测指挥部</h1>
            <p style="margin: 8px 0 0; opacity: 0.8; font-size: 13px;">Gmail 专用版 | 已优化 App 唤起协议</p>
        </div>

        <div style="padding: 20px;">
            <div style="background: #fff3e0; border-left: 4px solid #ff9800; padding: 12px; margin-bottom: 20px; font-size: 13px; color: #e65100;">
                <strong>💡 操作指引：</strong>请在<strong>手机端 Gmail</strong>点击下方卡片。点击后将直接唤起微信/小红书 App，避开电脑端的链接校验。
            </div>

            <h3 style="color: #333; font-size: 16px; border-bottom: 2px solid #6200EE; padding-bottom: 5px;">📍 微信自媒体 (点击唤起)</h3>
            <div style="display: flex; flex-wrap: wrap; gap: 10px; margin: 15px 0;">
                <a href="https://mp.weixin.qq.com/mp/appmsgalbum?__biz=MzI3MDUyODA3MA==&action=getalbum&album_id=1587829280459341825#wechat_redirect" 
                   style="flex: 1; min-width: 120px; background: white; padding: 15px; border-radius: 10px; text-align: center; text-decoration: none; border: 1px solid #eee; box-shadow: 0 2px 5px rgba(0,0,0,0.05);">
                    <div style="font-weight: bold; color: #07C160;">微信能量站</div>
                    <div style="font-size: 11px; color: #999; margin-top: 5px;">官方权威榜单</div>
                </a>
                <a href="weixin://dl/business/?t=XXXXX"  # 这是一个示意，微信搜一搜更稳
                   style="flex: 1; min-width: 120px; background: white; padding: 15px; border-radius: 10px; text-align: center; text-decoration: none; border: 1px solid #eee; box-shadow: 0 2px 5px rgba(0,0,0,0.05);">
                    <div style="font-weight: bold; color: #333;">小游戏情报局</div>
                    <div style="font-size: 11px; color: #999; margin-top: 5px;">爆款题材拆解</div>
                </a>
            </div>

            <h3 style="color: #333; font-size: 16px; border-bottom: 2px solid #ff2442; padding-bottom: 5px; margin-top: 25px;">📍 小红书专区 (点击唤起)</h3>
            <a href="xhsdiscover://user/94136983499" 
               style="display: block; background: white; padding: 20px; border-radius: 12px; text-decoration: none; border: 1px solid #eee; margin-top: 15px;">
                <div style="display: flex; align-items: center;">
                    <div style="background: #ff2442; color: white; width: 40px; height: 40px; border-radius: 50%; text-align: center; line-height: 40px; font-weight: bold; margin-right: 15px;">她</div>
                    <div>
                        <div style="font-weight: bold; color: #333;">她按开始键</div>
                        <div style="font-size: 12px; color: #666; margin-top: 3px;">查看博主最新的题材笔记 ></div>
                    </div>
                </div>
            </a>

            <div style="margin-top: 30px; border-top: 1px dashed #ccc; padding-top: 15px;">
                <p style="font-size: 11px; color: #bbb; text-align: center;">
                    🤖 自动化打捞日志：GitHub 海外 IP 仍受限，已切换为“直达卡片”模式。
                </p>
            </div>
        </div>
    </div>
    """

    sender = os.environ.get('EMAIL_USER')
    password = str(os.environ.get('EMAIL_PASS')).strip()
    receiver = 'tanweilin1987@gmail.com'
    
    msg = MIMEText(html, 'html', 'utf-8')
    msg['From'] = f"MiniGameCommander <{sender}>"
    msg['To'] = receiver
    msg['Subject'] = Header(f'🚀 小游戏题材指挥部 - {time.strftime("%m-%d")}', 'utf-8')
    
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.starttls()
            server.login(sender, password)
            server.sendmail(sender, [receiver], msg.as_string())
        print("✅ 指挥部邮件已送达")
    except Exception as e:
        print(f"❌ 发送失败: {e}")

if __name__ == "__main__":
    send_commander_report()
