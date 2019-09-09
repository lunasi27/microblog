from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_openid import OpenID
from config import basedir, ADMINS, MAIL_SERVER, MAIL_PORT, MAIL_USERNAME, MAIL_PASSWORD
from elasticsearch import Elasticsearch
import os

app = Flask(__name__)
# 在flask web service被创建后，读取config文件
app.config.from_object('config')
db = SQLAlchemy(app)
# Flask-openID需要一个存储临时文件的路径
lm = LoginManager()
lm.init_app(app)
# 告知login manager这个view允许用户登录
lm.login_view = 'login'
oid = OpenID(app, os.path.join(basedir, 'tmp'))
# 初始化全文搜索引擎
es = Elasticsearch(app.config.get('ES_HOSTS')) if app.config.get('ES_HOSTS') else None
if es:
    if not es.indices.exists(app.config.get('POSTS_FULL_TEXT')):
        es.indices.create(index=app.config.get('POSTS_FULL_TEXT'), body=app.config.get('MAPPING'))

from app import views, models

# 在非调试模式下，使用logging记录出错信息
if not app.debug:
    import logging
    # 使用邮件发送异常
    from logging.handlers import SMTPHandler
    credentials = None
    if MAIL_USERNAME or MAIL_PASSWORD:
        credentials = (MAIL_SERVER, MAIL_PASSWORD)
    # Python的logging模块自带SMTP功能，所以可以直接使用logging的SMTP handler
    mail_handler = SMTPHandler((MAIL_SERVER, MAIL_PORT), 'no-reply@'+MAIL_SERVER, ADMINS, 'microblog failure', credentials)
    mail_handler.setLevel(logging.ERROR)
    # Flask默认自带一个logger
    app.logger.addHandler(mail_handler)
# 如果你的部署环境没有打开SMTP服务，那么可以使用python自带的SMTP调试服务器顶上
# >>> python -m smtp -n -c DebuggingServer localhost:25
# 当这个邮件服务器运行后，应用程序发送的邮件将会被接受并显示在命令行窗口上。

    # 使用文件记录异常
    from logging.handlers import RotatingFileHandler
    file_handler = RotatingFileHandler('tmp/microblog.log', 'a', 1*1024*1024*1024, 10)
    file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('microblog startup')
