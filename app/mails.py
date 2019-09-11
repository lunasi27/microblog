from flask_mail import Message
from app import mail
from flask import render_template
from config import ADMINS
from app.decorators import async_
from app import app
import pdb


# 因为目前发送邮件是同步调用，如果发送邮件的人很多，或者邮件服务器的网络状况很差的时候，我们的web server会被邮件服务拖累
# 因此我们必须使用异步服务，来实现send_mail()立刻返回，发送邮件的工作将被移交到后台
@async_
def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)


def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    # flask_mail要求mail.sned()方法必须在flask的app_context中才可用
    # mail.send(msg)
    send_async_email(app, msg)


def follower_notification(followed, follower):
    send_email("[microblog] %s is now following you!" % follower.nickname, ADMINS[0],
        [followed.email],
        render_template("follower_email.txt", user=followed, follower=follower),
        render_template("follower_email.html", user=followed, follower=follower)
    )
    # 我们使用render_template()来渲染我们邮件