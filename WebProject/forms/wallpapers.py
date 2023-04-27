from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms import BooleanField, SubmitField, FileField
from wtforms.validators import DataRequired


class WallPapersForm(FlaskForm):
    title = StringField('Название', validators=[DataRequired()])
    file = FileField('Файл', validators=[DataRequired()])
    content = TextAreaField("Теги")
    # is_private = BooleanField("Личное")
    submit = SubmitField('Загрузить')

