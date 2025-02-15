from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField
from wtforms.validators import DataRequired, Regexp, EqualTo, NumberRange, Optional

class UserAddForm(FlaskForm):
    """Form for adding users."""

    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[Regexp(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$", message="Password must contain at least 8 characters, 1 uppercase letter, 1 lowercase letter, 1 number, and 1 special character.")
])
    confirm = PasswordField('Confirm Password', validators=[
        EqualTo('password', message='Passwords must match')
    ])

class LoginForm(FlaskForm):
    """Login form."""

    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password')

class ProductForm(FlaskForm):
    """Form for adding products."""

    name = StringField(u'Product not found? Please submit product name.', validators=[DataRequired()])

class SortForm(FlaskForm):
    """Sort By Form."""

    sort = SelectField(u'Sort By:', choices=[('','Please select'),('popular','Most popular'),('price_lh','Price: low to high'),('price_hl','Price: high to low'),('rating','Best rating'),('acne_score','Acne score: low to high'),('irritant_score','Irritant score: low to high'),('safety_score','Safety score: low to high')])