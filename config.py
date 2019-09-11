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
# BLOG每页要显示的消息数
POST_PER_PAGE = 3
# 配置全文搜索数据库Elsticsearch
ES_HOSTS = [{'host': '192.168.1.111', 'port': 9200}]
POSTS_FULL_TEXT = 'post'
MAPPING = {
    'mappings': {
        'properties': {
            'title': {
                'type': 'text',
                'analyzer': 'ik_max_word',
                'search_analyzer': 'ik_max_word'
            }
        }
    }
}

# 运行时出错后，发送邮件到管理员
# 错误处理代码，在程序中配置邮件服务器以及管理员邮箱
MAIL_SERVER = 'smtp.163.com'
MAIL_PORT = 465
MAIL_USE_TLS = False
MAIL_USE_SSL = True
MAIL_USERNAME = ''
MAIL_PASSWORD = ''
ADMINS = ['']
