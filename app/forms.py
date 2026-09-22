from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, EqualTo
class RegisterForm(FlaskForm):
    full_name=StringField('Full name', validators=[DataRequired(),Length(min=2,max=120)])
    email=StringField('Email', validators=[DataRequired(),Email(),Length(max=160)])
    password=PasswordField('Password', validators=[DataRequired(),Length(min=8,max=128)])
    confirm=PasswordField('Confirm password', validators=[DataRequired(),EqualTo('password')])
    submit=SubmitField('Create account')
class LoginForm(FlaskForm):
    email=StringField('Email', validators=[DataRequired(),Email()])
    password=PasswordField('Password', validators=[DataRequired()])
    submit=SubmitField('Log in')
