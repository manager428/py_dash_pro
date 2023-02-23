from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError,Optional


class AddUserForm(FlaskForm):
    username = StringField('Username',
                        validators=[DataRequired()])
    email = StringField('Email',
                        validators=[DataRequired()])
    temp_password = PasswordField('Temporary Password',
                        validators=[DataRequired()])
    first_name = StringField('First Name',
                        validators=[DataRequired()])
    last_name = StringField('Last Name',
                        validators=[DataRequired()])
    middle_name = StringField('Middle Name',
                        validators=[Optional()])                    
    dob = StringField('Dob',
                        validators=[Optional()])
    bmi = StringField('BMI',
                        validators=[Optional()])
    group = SelectField('Patient Group',
        choices=[('patient', 'Patient'), ('clinicians', 'Clinician'), ('admin', 'Admin')]
    )
    gender = SelectField('Gender',
        choices=[('M', 'Male'), ('F', 'Female')]
    )
    clinician = SelectField(u'Clinician', choices=[])
                   
    submit = SubmitField('Submit')

    def __init__(self, clinician=None):
        super().__init__()  
        if clinician: 
            self.clinician.choices =[(i, x) for i,x in enumerate(clinician)]


class UpdateUserForm(FlaskForm):
    first_name = StringField('Firat Name',
                        validators=[DataRequired()])
    last_name = StringField('Last Name',
                        validators=[DataRequired()])
    middle_name = StringField('Middle Name',
                        validators=[Optional()])
    dob = StringField('Dob',
                        validators=[Optional()])
    bmi = StringField('BMI',
                        validators=[Optional()])
    fitbitid = StringField('FITBIT',
                        validators=[Optional()])                    
    group = SelectField('Patient Group',
        choices=[('patient', 'Patient'), ('clinicians', 'Clinician'), ('admin', 'Admin')]
    )
    gender = SelectField('Gender',
        choices=[('M', 'Male'), ('F', 'Female')]
    )
    clinician = SelectField(u'Clinician', choices=[])
                   
    submit = SubmitField('Update ')

    def __init__(self, clinician=None):
        super().__init__()  
        if clinician: 
            self.clinician.choices =[(i, x) for i,x in enumerate(clinician)]