from flask import render_template, flash, redirect, session, url_for, request, g
from flask_login import login_user, logout_user, current_user, login_required
from app import app, db, lm, oid
from app.forms import LoginForm, RegistrationForm, EditForm, PostForm
from app.models import User, Post
from datetime import datetime
from config import POST_PER_PAGE
from app.forms import SearchForm
import pdb


@app.before_request
def before_request():
    # 全局变量current_user是被Flask-Login设置的，因此我们只需要把它赋值给g.user就好了
    # 这一步的作用是，在接受request之前提前填充g.user变量
    g.user = current_user
    if g.user.is_authenticated:
        # 每次页面发送请求后，都会在数据库更新浏览时间
        g.user.last_seen = datetime.utcnow()
        db.session.add(g.user)
        db.session.commit()
        # 因为我们几乎要在所有的页面都用到SearchForm的实例，与其在每个路由中都创建表单对象，然后再把对象传给模板
        # 不如，直接在将表单对象配置成全局变量。这样可以消除重复代码。
        # 还有一个好处，在模板中也能看到g变量，所以我们不需要显式的给模板传递Form
        g.search_form = SearchForm()


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
# 分页的时候需要API这边传入一个数字类型的page参数
@app.route('/index/<int:page>', methods=['GET', 'POST'])
@login_required
def index(page=1):
    # login_required装饰器保证，该页面只被已登录的用户看到
    user = g.user
    # g.user.followed_posts() 返回的是一个sqlalchemy对象，如果想检索所有数据，请使用all()函数。
    # 这里还存在一个问题"分页"，如果未来有成千上万条post数据，一次性显示明显不合适。因此我们需要分组或者分页显示。
    # Flask-SQLAlchemy天生就支持分页，使用函数paginate(页数从1开始, 每一页的条目数, 错误标志为真返回404为假返回空列表), paginate函数返回一个Pagination对象。该对象的items属性是blog列表。他还有其他很有意思的属性。
    # posts = g.user.followed_posts().all()
    # 我们不使用.items属性，而是直接使用Pagination对象，将这个对象传入模板。
    posts = g.user.followed_posts().paginate(page, POST_PER_PAGE, False)
    # posts = [{'author': {'nickname': 'John'},
    #           'body': 'Beautiful day in Portland!'},
    #          {'author': {'nickname': 'Suan'},
    #           'body': 'The Avengers moive was so cool!'}]
    form = PostForm()
    # 如果有提交动作
    if form.validate_on_submit():
        post = Post(body=form.post.data, timestamp=datetime.utcnow(), author=user)
        db.session.add(post)
        db.session.commit()
        flash('Your post is now live!')
        # 这里为什么不使用reander_template直接生成表单?因为考虑用户误操作的情况下（比如误刷新，浏览器回重新发送上一个请求，作为刷新浏览器的结果），浏览器冲突提交POST请求回造成数据的冗余。这不是我们预期的结果。
        # 有了重定向的话，那么浏览器最后一个收到的请求就是重定向，这并不会造成重复提交。
        return redirect(url_for('index'))
    return render_template('index.html', title='Home', form=form, user=user, posts=posts)


# 如果有method参数的话，视图接受GET和POST请求。如果不带method参数的话，只接收GET请求。
# oid.loginhandler的作用是告诉Flask-OpenID这是我们的登录视图。
@app.route('/login', methods=['GET', 'POST'])
@oid.loginhandler
def login():
    # 在flask中，有一个专门用来存储用户信息的对象g，g的全称是global
    # g对象在一次请求的所有地方都通用
    # session对夸request的，而g对象是在一次request中有效
    if g.user is not None and g.user.is_authenticated:
        # 如果是一个已经登录的用户的话，就不需要二次登录了
        return redirect(url_for('index'))
    # pdb.set_trace()
    form = LoginForm()
    # form.show()
    # 在第一次显示表单的时候，这个验证不会进来，只有在提交表单时，这个验证才会进来。如果提交表单时，openid==None，那么在页面上会有提示。
    if form.validate_on_submit():
        session['remember_me'] = form.remember_me.data
        if form.email.data:
            # 如果是以用户名密码形式登录，那么直接验证密码
            user = user = User.query.filter_by(email=form.email.data).first()
            if user is not None and user.check_password(form.password.data):
                remember_me = False
                if 'remember_me' in session:
                    remember_me = session['remember_me']
                    # 字典pop的时候，第二个参数是如果没有的默认值
                    session.pop('remember_me', None)
                # 登录
                login_user(user, remember=remember_me)
                return redirect(request.args.get('next') or url_for('index'))
        if form.openid.data:
            # oid.try_login被调用是为了触发用户使用Flask-OpenID认证，该函数接受两个参数(web表单提供的openid, 我们从openid提供者那么获得的数据项列表)
            return oid.try_login(form.openid.data, ask_for=['nickname', 'email'])
        # 收集所以数据，对字段进行验证，如果都通过的话吗，就会返回true，然后跳转回主页。
        # flash函数是一种快速的方式下呈现给用户页面上显示一个消息。我们使用它来做调试(在template中，取到flash message然后显示出来)。flash函数在生产服务器上也有其作用，比如快速给用户反馈。
        # flash('Login request for OpenID="' + form.openid.data + '", remember_me=' + str(form.remember_me.data))
        # return redirect('/index')
    return render_template('login.html', title='Sign In', form=form, providers=app.config['OPENID_PROVIDERS'])


@oid.after_login
def after_login(resp):
    # pdb.set_trace()
    resp.email = 'wanghao27@163.com'
    if resp.email is None or resp.email == '':
        # 验证登录的合法性，没有邮箱是不能登录的
        flash('Invalid login. Plase try again')
        return redirect(url_for('login'))
    user = User.query.filter_by(email=resp.email).first()
    if user is None:
        nickname = resp.nickname
        if nickname is None or nickname == '':
            nickname = resp.email.split('@')[0]
        # 防止出现重复的用户名
        nickname = User.make_unique_nickname(nickname)
        user = User(nickname=nickname, email=resp.email)
        db.session.add(user)
        db.session.commit()
    remember_me = False
    if 'remember_me' in session:
        remember_me = session['remember_me']
        # 字典pop的时候，第二个参数是如果没有的默认值
        session.pop('remember_me', None)
    # 登录
    login_user(user, remember=remember_me)
    # 如果next页面没有定义的话就会重定向到首页
    return redirect(request.args.get('next') or url_for('index'))


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(nickname=form.nickname.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are new a registered user!')
        return redirect(request.args.get('next') or url_for('index'))
    return render_template('register.html', title='Register', form=form)


@app.route('/user/<nickname>')
@app.route('/user/<nickname>/<int:page>')
@login_required
def user(nickname, page=1):
    user = User.query.filter_by(nickname=nickname).first()
    if user is None:
        flash('User ' + nickname + ' not found.')
        return redirect(url_for('index'))
    # 这里post是假数据，用来测试web页面的
    # posts = [
    #     {'author': user, 'body': 'Test post #1'},
    #     {'author': user, 'body': 'Test post #2'}
    # ]
    posts = user.posts.paginate(page, POST_PER_PAGE, False)
    return render_template('user.html', user=user, posts=posts)


@app.route('/edit', methods=['GET', 'POST'])
@login_required
def edit():
    form = EditForm(g.user.nickname)
    if form.validate_on_submit():
        g.user.nickname = form.nickname.data
        g.user.about_me = form.about_me.data
        db.session.add(g.user)
        db.session.commit()
        flash('Your changes has been saved.')
        return redirect(url_for('edit'))
    else:
        form.nickname.data = g.user.nickname
        form.about_me.data = g.user.about_me
    return render_template('edit.html', form=form)


@app.route('/follow/<nickname>')
@login_required
def follow(nickname):
    user = User.query.filter_by(nickname=nickname).first()
    if user is None:
        flash('User %s not found.' % nickname)
        return redirect(url_for('index'))
    if user == g.user:
        flash('You can\'t follow yourself.')
        return redirect(url_for('index'))
    u = g.user.follow(user)
    if u is None:
        flash('Cannot follow %s.' % nickname)
        return redirect(url_for('user', nickname=nickname))
    db.session.add(u)
    db.session.commit()
    flash('You are now following %s!' % nickname)
    return redirect(url_for('user', nickname=nickname))


@app.route('/unfollow/<nickname>')
@login_required
def unfollow(nickname):
    user = User.query.filter_by(nickname=nickname).first()
    if user is None:
        flash('User %s not found.' % nickname)
        return redirect(url_for('index'))
    if user == g.user:
        flash('You can\'t follow yourself.')
        return redirect(url_for('index'))
    u = g.user.follow(user)
    if u is None:
        flash('Cannot unfollow %s.' % nickname)
        return redirect(url_for('user', nickname=nickname))
    db.session.add(u)
    db.session.commit()
    flash('You have stopped following %s!' % nickname)
    return redirect(url_for('user', nickname=nickname))


@app.route('/search')
@login_required
def search():
    # 在其他表单中，我们使用validate_on_submit()方法来提交表单
    # 不幸的是，该方法只适用于POST，所以对于这个表单我们需要用form.validate()方式
    # 对于这个方式，他只验证字段值，而不检查数据是如何提交的。如果因为用户提交了空表单而验证失败
    # 我们只能重定向到首页。
    if not g.search_form.validate():
        return redirect(url_for('index'))
    page = request.args.get('page', 1, type=int)
    posts, total = Post.search(g.search_form.q.data, page, POST_PER_PAGE)
    # 计算下一页的页面URL
    next_url = url_for('search', q=g.search_form.q.data, page=page+1) \
        if total > page * POST_PER_PAGE else None
    # 计算上一页的页面URL
    prev_url = url_for('search', q=g.search_form.q.data, page=page-1) \
        if page > 1 else None
    return render_template('search', title=_('Search'), posts=posts,
    next_url=next_url, prev_url=prev_url)




# flask为应用程序提供的安装错误页的机制
@app.errorhandler(404)
def internal_error_404(error):
    # 这是用户自定义的错误处理响应页面
    return render_template('404.html')


# flask为应用程序提供的安装错误页的机制
@app.errorhandler(500)
def internal_error_500(error):
    # 这是用户自定义的错误处理响应页面
    db.session.rollback()
    return render_template('500.html')

