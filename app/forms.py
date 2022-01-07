from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, RadioField,SelectField , TextAreaField , BooleanField
from wtforms.validators import Length, EqualTo, Email, DataRequired, ValidationError

from app.models import User


class RegisterForm(FlaskForm):

    # validate under score will check and do validation - no need to use just need to right correctly
    def validate_email_address(self, email_address_to_check):
        user = User.query.filter_by(email_address=email_address_to_check.data).first()
        if user:
            raise ValidationError('Email address Exists')

    def validate_username(self, username_to_check):
        user = User.query.filter_by(username=username_to_check.data).first()
        if user:
            raise ValidationError('Username Exists')

    username = StringField(label=':שם משתמש', validators=[Length(min=9, max=9), DataRequired()])
    name = StringField(label=':שם מלא', validators=[Length(min=0, max=30), DataRequired()])
    email_address = StringField(label=':דואר אלקטורני', validators=[Email(), DataRequired()])
    password1 = PasswordField(label=':סיסמה', validators=[EqualTo('username'), DataRequired()])
    professor_name = SelectField(':שם מרצה', choices=[('דר צוקרמן', 'דר צוקרמן'), ('דר לאופר', 'דר לאופר'), ('דר גלזר', 'דר גלזר')])
    approval = BooleanField(label='אישור השתתפות בניסוי', validators=[DataRequired()])
    sumbit = SubmitField(label='הרשמה')


class LoginForm(FlaskForm):
    username = StringField(label=':שם משתמש', validators=[DataRequired()])
    password = PasswordField(label=':סיסמה', validators=[DataRequired()])
    submit = SubmitField(label='כניסה')


class RateForm(FlaskForm):
    q1 = TextAreaField(label=':q1', validators=[DataRequired()])
    q2 = TextAreaField(label=':q2', validators=[DataRequired()])
    q3 = TextAreaField(label=':q3', validators=[DataRequired()])
    q4 = TextAreaField(label=':q4', validators=[DataRequired()])
    q5 = TextAreaField(label=':q4', validators=[DataRequired()])
    rate = RadioField('Label',
                    choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')],
                    validators=[DataRequired()])

    submit = SubmitField(label='שליחה')



class ChangeText(FlaskForm):
    q1 = TextAreaField(label=':q1', validators=[DataRequired()])
    q2 = TextAreaField(label=':q2', validators=[DataRequired()])
    q3 = TextAreaField(label=':q3', validators=[DataRequired()])
    q4 = TextAreaField(label=':q4', validators=[DataRequired()])
    q5 = TextAreaField(label=':q4', validators=[DataRequired()])

    submit = SubmitField(label='שליחה')


class Compare2(FlaskForm):
    select = RadioField('groupnames',coerce= int,validators=[DataRequired()])
    submit = SubmitField(label='בחירה')
