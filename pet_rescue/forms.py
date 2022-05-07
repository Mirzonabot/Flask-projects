from ast import Sub
import email
from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Email,EqualTo

class SignUp(FlaskForm):
    full_name = StringField("Full name",validators=[InputRequired()])
    email = StringField("Email",validators=[InputRequired(),Email()])
    password = PasswordField("Password",validators=[InputRequired()])
    confirm_password = PasswordField("Confirm Password",validators=[InputRequired(),EqualTo("password")])
    submit = SubmitField("SignUp")


class LogIn(FlaskForm):
    email = StringField("Email",validators=[InputRequired(),Email()])
    password = PasswordField("Password",validators=[InputRequired()])
    submit = SubmitField("Login")

class PetForm(FlaskForm):
    name = StringField("Pet's Name", validators = [InputRequired()])
    age = StringField("Pet's Age", validators = [InputRequired()])
    bio = StringField("Pet's Bio", validators = [InputRequired()])
    pet_pic = FileField("Pet pic")
    submit = SubmitField("Submit")