from flask import render_template, flash, redirect, session, url_for, request, g
from flask_login import login_user, logout_user, current_user, login_required
from app import app, db, lm, oid
from app.forms import LoginForm, RegistrationForm, EditForm
from app.models import User
from datetime import datetime
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


@app.route('/')
@app.route('/index')
@login_required
def index():
    # login_required装饰器保证，该页面只被已登录的用户看到
    user = g.user
    posts = [{'author': {'nickname': 'John'},
              'body': 'Beautiful day in Portland!'},
             {'author': {'nickname': 'Suan'},
              'body': 'The Avengers moive was so cool!'}]
    return render_template('index.html', title='Home', user=user, posts=posts)


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
        return render_template('register.html', title='Register', form=form)


@app.route('/user/<nickname>')
@login_required
def user(nickname):
    user = User.query.filter_by(nickname=nickname).first()
    if user is None:
        flash('User ' + nickname + ' not found.')
        return redirect(url_for('index'))
    # 这里post是假数据，用来测试web页面的
    posts = [
        {'author': user, 'body': 'Test post #1'},
        {'author': user, 'body': 'Test post #2'}
    ]
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
