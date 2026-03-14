"""
邮件发送工具类
支持发送每日趋势报告邮件
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
import os
from datetime import datetime
from typing import List, Optional

class EmailSender:
    """邮件发送器"""
    
    def __init__(self, smtp_server: str = None, smtp_port: int = None, 
                 username: str = None, password: str = None):
        """初始化邮件配置"""
        self.smtp_server = smtp_server or os.getenv('SMTP_SERVER', 'smtp.qq.com')
        self.smtp_port = smtp_port or int(os.getenv('SMTP_PORT', 587))
        self.username = username or os.getenv('SMTP_USERNAME')
        self.password = password or os.getenv('SMTP_PASSWORD')
        
        if not all([self.smtp_server, self.username, self.password]):
            raise ValueError("请配置SMTP服务器信息")
    
    def send_daily_report(self, to_emails: List[str], report_data: dict) -> bool:
        """发送每日报告邮件"""
        try:
            # 创建邮件内容
            subject = f"TechPulse AI 每日趋势报告 - {report_data['report_date']}"
            
            # HTML邮件内容
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
                    .container {{ max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }}
                    .header {{ text-align: center; margin-bottom: 30px; color: #333; }}
                    .summary {{ background: #f0f8ff; padding: 20px; border-radius: 8px; margin-bottom: 20px; line-height: 1.6; }}
                    .recommendation {{ background: #f9f9f9; padding: 15px; margin: 10px 0; border-left: 4px solid #4a90e2; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🤖 TechPulse AI 每日趋势报告</h1>
                        <p>报告日期: {report_data['report_date']}</p>
                    </div>
                    
                    <div class="summary">
                        <h2>📊 技术趋势总结</h2>
                        <p>{report_data['summary']}</p>
                    </div>
                    
                    <h2>⭐ 推荐阅读</h2>
                    {self._format_recommendations(report_data.get('recommendations', []))}
                    
                    <p style="margin-top: 30px; color: #666; font-size: 0.9rem;">
                        此邮件由 TechPulse AI 自动发送，如需退订请回复此邮件。
                    </p>
                </div>
            </body>
            </html>
            """
            
            # 纯文本内容
            text_content = f"""
TechPulse AI 每日趋势报告 - {report_data['report_date']}

📊 技术趋势总结：
{report_data['summary']}

⭐ 推荐阅读：
{self._format_recommendations_text(report_data.get('recommendations', []))}

--
此邮件由 TechPulse AI 自动发送
            """
            
            # 发送邮件
            for email in to_emails:
                self._send_email(email, subject, text_content, html_content)
            
            return True
            
        except Exception as e:
            print(f"发送邮件失败: {e}")
            return False
    
    def _format_recommendations(self, recommendations: List[dict]) -> str:
        """格式化推荐内容为HTML"""
        if not recommendations:
            return "<p>今日无推荐文章</p>"
        
        html = ""
        for rec in recommendations:
            html += f"""
            <div class="recommendation">
                <h3>{rec['title']}</h3>
                <p>{rec['reason']}</p>
            </div>
            """
        return html
    
    def _format_recommendations_text(self, recommendations: List[dict]) -> str:
        """格式化推荐内容为纯文本"""
        if not recommendations:
            return "今日无推荐文章"
        
        text = ""
        for i, rec in enumerate(recommendations, 1):
            text += f"{i}. {rec['title']}\n   理由: {rec['reason']}\n\n"
        return text
    
    def _send_email(self, to_email: str, subject: str, text_content: str, html_content: str):
        """发送单封邮件"""
        # 创建邮件对象
        msg = MIMEMultipart('alternative')
        msg['From'] = self.username
        msg['To'] = to_email
        msg['Subject'] = Header(subject, 'utf-8')
        
        # 添加纯文本和HTML版本
        part1 = MIMEText(text_content, 'plain', 'utf-8')
        part2 = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(part1)
        msg.attach(part2)
        
        # 连接SMTP服务器并发送
        with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
            server.starttls()  # 启用TLS加密
            server.login(self.username, self.password)
            server.send_message(msg)
        
        print(f"邮件发送成功: {to_email}")

# 邮件配置示例
# 环境变量配置：
# SMTP_SERVER=smtp.qq.com
# SMTP_PORT=587
# SMTP_USERNAME=your_email@qq.com
# SMTP_PASSWORD=your_smtp_password
# EMAIL_RECIPIENTS=user1@example.com,user2@example.com

# 测试邮件发送
# sender = EmailSender()
# success = sender.send_daily_report(
#     ['nihao@outlook.com'],  # 测试收件人
#     {
#         'report_date': datetime.now().strftime('%Y-%m-%d'),
#         'summary': '这是测试邮件内容',
#         'recommendations': [
#             {'title': '测试文章1', 'reason': '测试推荐理由1'},
#             {'title': '测试文章2', 'reason': '测试推荐理由2'}
#         ]
#     }
# )