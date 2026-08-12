from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DateTimeField, SubmitField
from wtforms.validators import DataRequired, Length, Optional

class TaskForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description', validators=[Optional()])
    priority = SelectField('Priority', choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High')
    ], default='medium')
    due_date = DateTimeField('Due Date', format='%Y-%m-%dT%H:%M', validators=[Optional()])
    submit = SubmitField('Save Task')