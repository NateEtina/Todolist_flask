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
    reminder_date = DateTimeField('Reminder', format='%Y-%m-%dT%H:%M', validators=[Optional()])
    project_id = SelectField('Project', choices=[], coerce=int, validators=[Optional()])
    depends_on_id = SelectField('Depends On', choices=[], coerce=int, validators=[Optional()])
    submit = SubmitField('Save Task')

class ProjectForm(FlaskForm):
    name = StringField('Project Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[Optional()])
    color = SelectField('Color', choices=[
        ('primary', 'Blue'),
        ('success', 'Green'),
        ('danger', 'Red'),
        ('warning', 'Yellow'),
        ('info', 'Cyan'),
        ('purple', 'Purple')
    ], default='primary')
    submit = SubmitField('Save Project')
