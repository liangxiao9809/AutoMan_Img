import requests
import smtplib
import os
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication


def log(*args, **kwargs):
    """带时间戳的日志输出（红色）"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\033[91m[{timestamp}]\033[0m", *args, **kwargs)


def send_ding_message(content):
    """
    发送钉钉消息
    
    Args:
        content: 消息内容
    """
    webhook = "https://oapi.dingtalk.com/robot/send?access_token=55125ed9e75886d1683d38e9cd26acfa2755215fb8594da0385e99691474b03e"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    prefix = "警告"

    data = {
        "msgtype": "text",
        "text": {
            "content": f"{prefix}: {content}"
        }
    }

    try:
        response = requests.post(webhook, json=data, headers=headers, timeout=10)
        result = response.json()
        if result.get("errcode") == 0:
            log(f"钉钉消息发送成功: {content}")
        else:
            log(f"钉钉消息发送失败: errcode={result.get('errcode')}, errmsg={result.get('errmsg')}")
    except Exception as e:
        log(f"钉钉消息发送失败: {e}")


def send_ding_image(image_url, text=""):
    """
    发送钉钉图片消息（Markdown方式）
    
    Args:
        image_url: 图片的公网可访问URL
        text: 图片下方的说明文字（可选）
    """
    webhook = "https://oapi.dingtalk.com/robot/send?access_token=55125ed9e75886d1683d38e9cd26acfa2755215fb8594da0385e99691474b03e"
    
    headers = {
        "Content-Type": "application/json"
    }

    content = f"![图片]({image_url})"
    if text:
        content += f"\n\n{text}"

    data = {
        "msgtype": "markdown",
        "markdown": {
            "title": "图片消息",
            "text": content
        }
    }

    try:
        response = requests.post(webhook, json=data, headers=headers, timeout=10)
        result = response.json()
        if result.get("errcode") == 0:
            log(f"钉钉图片发送成功: {image_url}")
        else:
            log(f"钉钉图片发送失败: errcode={result.get('errcode')}, errmsg={result.get('errmsg')}")
    except Exception as e:
        log(f"钉钉图片发送失败: {e}")


def send_email(to, subject, body, attachments=None):
    """
    发送邮件，支持附件
    
    Args:
        to: 收件人邮箱地址（单个字符串或列表）
        subject: 邮件主题
        body: 邮件正文（支持HTML）
        attachments: 附件文件路径列表（可选）
    """
    mail_user = os.environ.get("MAIL_USER")
    mail_pass = os.environ.get("MAIL_PASS")
    mail_host = os.environ.get("MAIL_HOST")
    mail_port = int(os.environ.get("MAIL_PORT", 465))
    mail_use_ssl = os.environ.get("MAIL_USE_SSL", "true").lower() == "true"

    if not all([mail_user, mail_pass, mail_host]):
        log("邮件发送失败: 缺少环境变量配置（MAIL_USER/MAIL_PASS/MAIL_HOST）")
        return

    msg = MIMEMultipart()
    msg["From"] = mail_user
    msg["To"] = to if isinstance(to, str) else ",".join(to)
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "html" if "<" in body else "plain", "utf-8"))

    if attachments:
        for file_path in attachments:
            if os.path.exists(file_path):
                with open(file_path, "rb") as f:
                    part = MIMEApplication(f.read())
                    part.add_header("Content-Disposition", "attachment", filename=os.path.basename(file_path))
                    msg.attach(part)
                log(f"添加附件: {file_path}")
            else:
                log(f"附件不存在: {file_path}")

    try:
        if mail_use_ssl:
            server = smtplib.SMTP_SSL(mail_host, mail_port)
        else:
            server = smtplib.SMTP(mail_host, mail_port)
            server.starttls()
        
        server.login(mail_user, mail_pass)
        server.sendmail(mail_user, to, msg.as_string())
        server.quit()
        log(f"邮件发送成功: {to}")
    except Exception as e:
        log(f"邮件发送失败: {e}")


def upload_to_beeimg(file_path, apikey=None):
    """
    上传图片到蜜蜂图床
    
    Args:
        file_path: 本地图片文件路径
        apikey: API密钥（可选）
    
    Returns:
        str: 上传后的图片URL，失败返回None
    """
    api_url = "https://beeimg.com/api/upload/file/json/"
    
    if not os.path.exists(file_path):
        log(f"图片文件不存在: {file_path}")
        return None
    
    try:
        with open(file_path, "rb") as f:
            files = {"file": (os.path.basename(file_path), f)}
            data = {}
            if apikey:
                data["apikey"] = apikey
            
            response = requests.post(api_url, files=files, data=data, timeout=30)
            result = response.json()
            
            if result.get("status") == "success" and result.get("image"):
                image_url = result["image"].get("url") or result["image"].get("medium") or result["image"].get("thumb")
                if image_url:
                    log(f"图片上传成功: {image_url}")
                    return image_url
                else:
                    log(f"图片上传成功但未返回URL: {result}")
                    return None
            else:
                error = result.get("error", {}).get("message", "未知错误")
                log(f"图片上传失败: {error}")
                return None
    except Exception as e:
        log(f"图片上传失败: {e}")
        return None
