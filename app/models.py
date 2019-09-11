from app import db, lm
# 我们存储在数据库中的数据将会以类的集合的形式来表示，我们称之为数据库模型。
# ORM层需要做的事情就是将以这些类创建的对象映射到合适的数据表中的具体行上。
from werkzeug.security import generate_password_hash, check_password_hash
from hashlib import md5
from app.search import add_to_index, remove_from_index, query_index
import pdb


followers = db.Table(
    # 定义多对多关系的辅助表，因为是辅助表所以不用把它定义成一个类
    'followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime)
    # 在USER表中建立多对多关系（这里是关注与被关注人的关系）
    followed = db.relationship(
        'User',
        # 指定这个对应关系的辅助表
        secondary=followers,
        # 确定辅助表中的两个外键与当前User表之间的对应关系
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        # 指定从右侧返回的返回的字段名及查询类型
        backref=db.backref('followers', lazy='dynamic'),
        # 这个和上面的那个一个意思，只有特定请求的时候才会去查询。这样做是出于性能的考虑。
        lazy='dynamic'
    )

    def __repr__(self):
        # 这个方法是告诉python该如何打印这个类
        return '<User %r>' % (self.nickname)

    @property
    def is_authenticated(self):
        # 一般而言这个方法只返回True，除非因为某些原因账户不被认证
        return True

    @property
    def is_active(self):
        # 除非账号被禁用，否则直接返回True
        return True

    @property
    def is_anonymous(self):
        # 匿名用户不允许登录系统
        return True

    def get_id(self):
        return str(self.id)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if self.password_hash is None:
            return False
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        # 我们使用Gravatar的头像服务构建系统，如果未来
        return 'http://www.gravatar.com/avatar/' + md5(self.email.encode('utf-8')).hexdigest() + '?/d=mm&s=' + str(size)

    @staticmethod
    def make_unique_nickname(nickname):
        if User.query.filter_by(nickname=nickname).first() is None:
            return nickname
        version = 2
        while True:
            new_nickname = nickname + str(version)
            if User.query.filter_by(nickname=new_nickname).first() is None:
                break
            version += 1
        return new_nickname

    # 添加和删除关注者
    def follow(self, user):
        if not self.is_following(user):
            # 这个里使用append是因为followed是User的辅助表，它属于User对象，它是User对象维护的一个列表。所以我们需要在操作完成后，返回user对象，然后再调用数据库去update它。
            self.followed.append(user)
            return self

    def unfollow(self, user):
        if self.is_following(user):
            # 这个里使用remove是因为followed是User的辅助表，它属于User对象，它是User对象维护的一个列表。所以我们需要在操作完成后，返回user对象，然后再调用数据库去update它。
            self.followed.remove(user)
            return self

    def is_following(self, user):
        return self.followed.filter(followers.c.followed_id == user.id).count() > 0

    def followed_posts(self):
        return Post.query.join(followers, (followers.c.followed_id == Post.user_id)).filter(followers.c.follower_id == self.id).order_by(Post.timestamp.desc())


# user_loader回调函数
# 主要是通过获取user对象存储到session中，自己实现最好启用缓存。
@lm.user_loader
def load_user(id):
    # 从数据库找到user对象
    return User.query.get(int(id))


# 整合ES与Database的钩子类，我们把Mixin类作为一个基类整合到Post模型中
class SearchableMixin():
    @classmethod
    def search(cls, expression, page, per_page):
        ids, total = query_index(cls.__tablename__, expression, page, per_page)
        if total == 0:
            return cls.query.filter_by(id=0), 0
        when = []
        for i in range(len(ids)):
            when.append((ids[i], i))
        return cls.query.filter(cls.id.in_(ids)).order_by(
            db.case(when, value=cls.id)), total

    @classmethod
    def before_commit(cls, session):
        # 于修改提交前，保存现场。因为一旦提交后，所有obj就都不可用了
        session._changes = {
            'add': [obj for obj in session.new if isinstance(obj, cls)],
            'update': [obj for obj in session.dirty if isinstance(obj, cls)],
            'delete': [obj for obj in session.deleted if isinstance(obj, cls)]
        }

    @classmethod
    def after_commit(cls, session):
        # 在提交成功后，是合适的时间把之前提交的修改同步到ES
        for obj in session._changes['add']:
            add_to_index(cls.__tablename__, obj)
        for obj in session._changes['update']:
            add_to_index(cls.__tablename__, obj)
        for obj in session._changes['delete']:
            remove_from_index(cls.__tablename__, obj)
        session._changes = None

    @classmethod
    def reindx(cls):
        # 这是一个辅助方法，用于一次性的加载数据库中的数据到ES
        for obj in cls.query:
            add_to_index(cls.__tablename__, obj)


class Post(SearchableMixin, db.Model):
    # 这个字段包含了所有能被搜索并且建立索引的字段。在我们的例子中，我们只要索引blog的body字段。
    __searchable__ = ['body']
    # Post对象中的可用字段
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Post %r>' % (self.body)


# 注册监听函数
# 注意：这里的监听函数不在Post类里面，而在Post类的后面
db.event.listen(db.session, 'before_commit', Post.before_commit)
db.event.listen(db.session, 'after_commit', Post.after_commit)
