import smtplib
import os
import time
from email.mime.text import MIMEText
from email.header import Header

def send_dashboard():
    # 彻底弃用易报错的抓取逻辑，改用官方永久稳定的数据接口
    html = """
    <div style="max-width: 600px; margin: 0 auto; font-family: 'Microsoft YaHei', sans-serif; border: 1px solid #eef2f1; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
        <div style="background: linear-gradient(135deg, #07C160 0%, #10ad57 100%); color: white; padding: 30px 20px; text-align: center;">
            <h1 style="margin: 0; font-size: 22px; letter-spacing: 1px;">🎮 小游戏官方数据看板</h1>
            <p style="margin: 8px 0 0; opacity: 0.85; font-size: 13px;">每日准时推送 · 官方权威渠道直达</p>
        </div>
        
        <div style="padding: 25px; background: #ffffff;">
            <div style="margin-bottom: 25px;">
                <div style="display: flex; align-items: center; margin-bottom: 12px;">
                    <span style="background: #07C160; width: 4px; height: 18px; display: inline-block; margin-right: 10px; border-radius: 2px;"></span>
                    <h3 style="margin: 0; color: #333; font-size: 16px;">微信官方数据源 (最权威)</h3>
                </div>
                <a href="https://mp.weixin.qq.com/mp/appmsgalbum?__biz=MzI3MDUyODA3MA==&action=getalbum&album_id=1587829280459341825#wechat_redirect" 
                   style="display: block; background: #f6fbf8; border: 1px solid #e1f2e9; padding: 15px; border-radius: 10px; text-decoration: none; margin-bottom: 10px;">
                    <strong style="color: #07C160; font-size: 14px;">📈 微信小游戏周榜/月榜汇总</strong>
                    <div style="color: #666; font-size: 12px; margin-top: 4px;">由腾讯官方“小游戏能量站”发布，包含活跃与买量数据。</div>
                </a>
            </div>

            <div style="margin-bottom: 25px;">
                <div style="display: flex; align-items: center; margin-bottom: 12px;">
                    <span style="background: #FF0050; width: 4px; height: 18px; display: inline-block; margin-right: 10px; border-radius: 2px;"></span>
                    <h3 style="margin: 0; color: #333; font-size: 16px;">抖音官方趋势源</h3>
                </div>
                <a href="https://trendinsight.oceanengine.com/arithmetic-index" 
                   style="display: block; background: #fff5f8; border: 1px solid #ffe1e9; padding: 15px; border-radius: 10px; text-decoration: none;">
                    <strong style="color: #FF0050; font-size: 14px;">🎵 巨量算数 - 抖音游戏热度指数</strong>
                    <div style="color: #666; font-size: 12px; margin-top: 4px;">实时查看抖音爆款题材、热门游戏关键词趋势。</div>
                </a>
            </div>

            <div style="padding-top: 15px; border-top: 1px dashed #eee;">
                <h4 style="color: #999; font-size: 13px; margin-bottom: 10px;">其他免费参考：</h4>
                <div style="display: flex; justify-content: space-between;">
                    <a href="https://www.gamelook.com.cn/" style="color: #555; font-size: 12px; text-decoration: underline;">GameLook 官网</a>
                    <a href="http://www.sykong.com/" style="color: #555; font-size: 12px; text-decoration: underline;">手游那点事</a>
                    <a href="https://www.vrtuoluo.cn/" style="color: #555; font-size: 12px; text-decoration: underline;">游戏陀螺</a>
                </div>
            </div>
        </div>
        
        <div style="background: #fcfcfc; padding: 15px; text-align: center; font-size: 11px; color: #bbb; border-top: 1px solid #f0f0f0;">
            由于第三方媒体封锁自动打捞，已切换为官方入口直达模式。
        </div>
    </div>
    """
    
    sender = os.environ.get('EMAIL_USER')
    password = str(os.environ.get('EMAIL_PASS')).strip()
    receiver = '249869251@qq.com'
    
    msg = MIMEText(html, 'html', 'utf-8')
    msg['From'] = f"GameDataBot <{sender}>"
    msg['To'] = receiver
    msg['Subject'] = Header(f'🚀 小游戏官方榜单看板 - {time.strftime("%m-%d")}', 'utf-8')

    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.starttls()
            server.login(sender, password)
            server.sendmail(sender, [receiver], msg.as_string())
        print("✅ 看板发送成功")
    except Exception as e:
        print(f"❌ 失败: {e}")

if __name__ == "__main__":
    send_dashboard()
