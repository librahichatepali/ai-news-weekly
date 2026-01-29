import smtplib
import os
import time
from email.mime.text import MIMEText
from email.header import Header

def send_mobile_command_center():
    # 采用高对比度卡片设计，专门适配手机 Gmail 屏幕
    html = """
    <div style="max-width: 450px; margin: 0 auto; font-family: sans-serif; background: #ffffff;">
        <div style="background: #000000; color: #ffffff; padding: 25px 15px; text-align: center; border-radius: 15px 15px 0 0;">
            <h2 style="margin: 0; font-size: 20px;">🎮 小游戏题材监测 (手机专用)</h2>
            <p style="margin: 5px 0 0; font-size: 12px; color: #999;">请在手机 Gmail App 中操作以避开 404</p>
        </div>

        <div style="padding: 15px; border: 1px solid #eeeeee; border-top: none; border-radius: 0 0 15px 15px;">
            <div style="margin-bottom: 25px;">
                <h3 style="font-size: 15px; color: #07C160; border-left: 4px solid #07C160; padding-left: 10px; margin-bottom: 12px;">微信公众号 (直达)</h3>
                
                <a href="https://mp.weixin.qq.com/mp/appmsgalbum?__biz=MzI3MDUyODA3MA==&action=getalbum&album_id=1587829280459341825#wechat_redirect" 
                   style="display: block; background: #f6fbf8; padding: 15px; border-radius: 10px; text-decoration: none; border: 1px solid #e1f2e9; margin-bottom: 10px;">
                    <div style="font-weight: bold; color: #333; font-size: 14px;">📈 微信小游戏能量站 (官方)</div>
                    <div style="color: #666; font-size: 12px; margin-top: 4px;">官方往期所有榜单合集 ></div>
                </a>

                <a href="https://mp.weixin.qq.com/mp/appmsgalbum?__biz=MzA3MDU3OTUzNQ==&action=getalbum&album_id=1626019970112421890#wechat_redirect" 
                   style="display: block; background: #f6fbf8; padding: 15px; border-radius: 10px; text-decoration: none; border: 1px solid #e1f2e9;">
                    <div style="font-weight: bold; color: #333; font-size: 14px;">🗞️ 游戏日报 · 小游戏专题</div>
                    <div style="color: #666; font-size: 12px; margin-top: 4px;">行业热点与题材拆解合集 ></div>
                </a>
            </div>

            <div>
                <h3 style="font-size: 15px; color: #ff2442; border-left: 4px solid #ff2442; padding-left: 10px; margin-bottom: 12px;">小红书博主</h3>
                <a href="https://www.xiaohongshu.com/user/profile/5df0a6990000000001000695" 
                   style="display: block; background: #fff5f6; padding: 15px; border-radius: 10px; text-decoration: none; border: 1px solid #ffe1e5;">
                    <div style="font-weight: bold; color: #333; font-size: 14px;">📕 她按开始键 (题材复盘)</div>
                    <div style="color: #666; font-size: 12px; margin-top: 4px;">点击在小红书 App 中查看博主主页 ></div>
                </a>
            </div>
        </div>
        
        <div style="text-align: center; padding: 20px; font-size: 11px; color: #bbb;">
            由于 GitHub 物理封锁，目前采用“入口直达”模式。
        </div>
    </div>
    """

    sender = os.environ.get('EMAIL_USER')
    password = str(os.environ.get('EMAIL_PASS')).strip()
    receiver = 'tanweilin1987@gmail.com'
    
    msg = MIMEText(html, 'html', 'utf-8')
    msg['From'] = f"MiniGameCommander <{sender}>"
    msg['To'] = receiver
    msg['Subject'] = Header(f'🚀 小游戏题材直达看板 - {time.strftime("%m-%d")}', 'utf-8')
    
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.starttls()
            server.login(sender, password)
            server.sendmail(sender, [receiver], msg.as_string())
        print("✅ 指挥部邮件已送达")
    except Exception as e:
        print(f"❌ 发送失败: {e}")

if __name__ == "__main__":
    send_mobile_command_center()
