import os

# 跨站请求伪造的保护--安全性配置
CSRF_ENABLED = True
SECRET_KEY = 'You-will-never-guess'

OPENID_PROVIDERS = [
    {'name': 'Google', 'url': 'https://accounts.google.com'},
    {'name': 'Yahoo', 'url': 'https://me.yahoo.com'},
    {'name': 'AOL', 'url': 'http://openid.aol.com/<username>'},
    {'name': 'Flickr', 'url': 'http://www.flickr.com/<unsername>'},
    {'name': 'MyOpenId', 'url': 'https://www.myopenid.com'}
]

basedir = os.path.abspath(os.path.dirname(__file__))
# 数据库的连接信息
DB_USER_NAME = 'postgres'
DB_PASSWD = '123456'
DB_HOST = 'localhost'
DB_NAME = 'product'
SQLALCHEMY_DATABASE_URI = 'postgresql+psycopg2://{}:{}@{}/{}'.format(DB_USER_NAME, DB_PASSWD, DB_HOST, DB_NAME)
# 这是一个文件夹，我们会把migrate的数据文件放在这里
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')
# 这条语句用来消除一个sqlalchemy的warning
SQLALCHEMY_TRACK_MODIFICATIONS = True

# 运行时出错后，发送邮件到管理员
# 错误处理代码，在程序中配置邮件服务器以及管理员邮箱
MAIL_SERVER = 'localhost'
MAIL_PORT = 25
MAIL_USERNAME = None
MAIL_PASSWORD = None
ADMINS = ['wanghao27@163.com']
