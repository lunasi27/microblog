from flask_wtf import FlaskForm
from flask import request
from wtforms import StringField, BooleanField, PasswordField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo, Length
from app.models import User


class LoginForm(FlaskForm):
    email = StringField('Email')
    password = PasswordField('Password')
    openid = StringField('openid')
    remember_me = BooleanField('remember_me', default=False)

    # 因为email password或者openid两种验证方式只能有一种有效，所以我们需要自己写validate函数
    # 重写的validate函数不需要显式的调用，在on_submit的时候回隐式调用
    def validate_loginmethod(self):
        if self.email.data and self.password.data and not self.openid.data:
            pass
        elif not self.email.data and not self.password.data and self.openid.data:
            pass
        else:
            raise ValidationError('Please login with Email+Password or OpenID.')


class RegistrationForm(FlaskForm):
    nickname = StringField('Nickname', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, user_name):
        user = User.query.filter_by(username=user_name.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')


class EditForm(FlaskForm):
    nickname = StringField('nickname', validators=[DataRequired()])
    about_me = TextAreaField('about_me', validators=[Length(min=0, max=140)])

    def __init__(self, original_nickname, *args, **kwargs):
        FlaskForm.__init__(self, *args, **kwargs)
        self.original_nickname = original_nickname

    def validate(self):
        # 重写了EditForm的validate方法
        if not FlaskForm.validate(self):
            return False
        if self.nickname.data == self.original_nickname:
            return True
        user = User.query.filter_by(nickname=self.nickname.data).first()
        if user:
            # 发现重新命名的user已经存在
            self.nickname.errors.append('This nickname is already in use. Please choose another one.')
            return False
        return True


class PostForm(FlaskForm):
    post = StringField('post', validators=[DataRequired()])


class SearchForm(FlaskForm):
    # SearchForm例如google/baidu这种都是使用GET方法提交表单而不是POST，所以我们这里需要特别配置一下
    # 首先，这里没有submit按钮，当有文本字段的时候，按下Enter键默认提交Form
    q = StringField('Search', validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        if 'formdata' not in kwargs:
            # formdata参数决定从哪里提交表单，缺省情况下是使用request.form，这是Flask放置POST请求的地方
            # 为了采用GET方法，我们需要将Flask-WTF指向request.args，这个是Flask写查询字符串参数的地方
            kwargs['formdata'] = request.args
        if 'csrf_enabled' not in kwargs:
            # 我们之前为表添加了csrf保护，包含了一个CSRF标记，该标记通过模板中的form.hidden_tag()构造添加到表单中
            # 现在因为我们要使用GET方法，所以需要禁用CSRF，忽略此表单的CSRF验证
            kwargs['csrf_enable'] = False
        super(SearchForm, self).__init__(*args, **kwargs)
