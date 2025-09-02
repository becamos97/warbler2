from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, Optional, URL

class SignupForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(max=30)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=100)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    image_url = StringField("Image URL", validators=[Optional(), URL()])

class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])

class MessageForm(FlaskForm):
    text = TextAreaField("Text", validators=[DataRequired(), Length(max=140)])

class EditProfileForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(max=30)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=100)])
    image_url = StringField("Image URL", validators=[Optional(), URL()])
    header_image_url = StringField("Header Image URL", validators=[Optional(), URL()])
    bio = TextAreaField("Bio", validators=[Optional(), Length(max=280)])  # <--
    location = StringField("Location", validators=[Optional(), Length(max=50)])
    password = PasswordField("Confirm with Password", validators=[DataRequired()])