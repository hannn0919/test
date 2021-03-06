from flask import redirect, render_template, url_for, flash
from flask.views import MethodView
from flask_login import current_user
from flask_wtf import FlaskForm

from wtforms import SubmitField, PasswordField
from wtforms.validators import InputRequired, Length, EqualTo, ValidationError

from app import bcrypt

class PasswordView(MethodView):
    def get(self):
        form = PasswordForm()

        return render_template('user/account/password.html', form=form)
    def post(self):
        form = PasswordForm()
        if form.validate_on_submit():
            current_user.password = bcrypt.generate_password_hash(form.password.data).decode()
            current_user.save()
            flash('修改成功')

            return redirect(url_for('user.password'))
        return render_template('user/account/password.html', form=form)



def validate_old_password(form, oldPassword):
    if bcrypt.check_password_hash(current_user.password, oldPassword.data) == False:
        raise ValidationError('密碼錯誤')

class PasswordForm(FlaskForm):
    old_password = PasswordField("舊密碼", validators=[InputRequired(), Length(min=6,max=20), validate_old_password])
    password = PasswordField("新密碼", validators=[InputRequired(), Length(min=6,max=20)])
    confirm  = PasswordField("確認新密碼", validators=[
        InputRequired(),
        Length(min=6,max=20),
        EqualTo('password', "Password must match")])
    submit = SubmitField('確認')