#!flask/venv/bin/pyhton

import unittest
import sys
sys.path.append('/home/haow/microblog')
from app import app, db
from app.models import User, Post
import datetime
import pdb


class TestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        DB_USER_NAME = 'postgres'
        DB_PASSWD = '123456'
        DB_HOST = 'localhost'
        DB_NAME = 'test'
        app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://{}:{}@{}/{}'.format(DB_USER_NAME, DB_PASSWD, DB_HOST, DB_NAME)
        self.app = app.test_client()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_avatar(self):
        u = User(nickname='John', email='john@example.com')
        avatar = u.avatar(128)
        expected = 'http://www.gravatar.com/avatar/d4c74594d841139328695756648b6bd6'
        assert avatar[0:len(expected)] == expected

    def test_make_unique_nickname(self):
        u = User(nickname='John', email='john@example.com')
        db.session.add(u)
        db.session.commit()
        nickname = User.make_unique_nickname('John')
        assert nickname != 'John'
        u = User(nickname=nickname, email='susan@example.com')
        db.session.add(u)
        db.session.commit()
        nickname2 = User.make_unique_nickname('John')
        assert nickname2 != 'John'
        assert nickname2 != nickname

    def test_follow(self):
        u1 = User(nickname='john', email='john@example.com')
        u2 = User(nickname='susan', email='susan@example.com')
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        assert u1.unfollow(u2) is None
        u = u1.follow(u2)
        db.session.add(u)
        db.session.commit()
        # 已经关注过了，所以这次应该返回None
        assert u1.follow(u2) is None
        assert u1.is_following(u2)
        # 已经有了一个粉丝
        assert u1.followed.count() == 1
        assert u1.followed.first().nickname == 'susan'
        # 因为u1关注了u2，所以u2有了一个粉丝
        assert u2.followers.count() == 1
        assert u2.followers.first().nickname == 'john'
        u = u1.unfollow(u2)
        assert u is not None
        db.session.add(u)
        db.session.commit()
        assert u1.is_following(u2) is False
        assert u1.followed.count() == 0
        assert u2.followers.count() == 0

    def test_follow_posts(self):
        # 创建4个用户
        u1 = User(nickname='john', email='john@example')
        u2 = User(nickname='susan', email='susan@example')
        u3 = User(nickname='mary', email='mary@example')
        u4 = User(nickname='david', email='david@example')
        db.session.add(u1)
        db.session.add(u2)
        db.session.add(u3)
        db.session.add(u4)
        # 创建博客
        utcnow = datetime.datetime.utcnow()
        p1 = Post(body='Post from john', author=u1, timestamp=utcnow+datetime.timedelta(seconds=1))
        p2 = Post(body='Post from susan', author=u2, timestamp=utcnow+datetime.timedelta(seconds=2))
        p3 = Post(body='Post from mary', author=u3, timestamp=utcnow+datetime.timedelta(seconds=3))
        p4 = Post(body='Post from david', author=u4, timestamp=utcnow+datetime.timedelta(seconds=4))
        db.session.add(p1)
        db.session.add(p2)
        db.session.add(p3)
        db.session.add(p4)
        # 到这里算是完成了一次完整的用例生成
        db.session.commit()
        # 开始设置followers
        u1.follow(u1)
        u1.follow(u2)
        u1.follow(u4)
        u2.follow(u2)
        u2.follow(u3)
        u3.follow(u3)
        u3.follow(u4)
        u4.follow(u4)
        db.session.commit()
        # 检查大V的博客是否已经显示出来了
        f1 = u1.followed_posts().all()
        f2 = u2.followed_posts().all()
        f3 = u3.followed_posts().all()
        f4 = u4.followed_posts().all()
        assert len(f1) == 3
        assert len(f2) == 2
        assert len(f3) == 2
        assert len(f4) == 1
        assert f1 == [p4, p2, p1]
        assert f2 == [p3, p2]
        assert f3 == [p4, p3]
        assert f4 == [p4]


if __name__ == '__main__':
    unittest.main()
