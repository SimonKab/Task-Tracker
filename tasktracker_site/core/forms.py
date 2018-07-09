from django import forms
import datetime

class TaskForm(forms.Form):
    priority_choices = [('low', 'low'), ('normal', 'normal'), 
                        ('high', 'high'), ('highest', 'highest')]
    datetime_input_formats = ['%d.%m.%Y %H:%M']

    title = forms.CharField(label='Title', max_length=256, required=True)
    description = forms.CharField(label='Description', required=False)
    priority = forms.ChoiceField(choices=priority_choices,
                                required=False)
    supposed_start = forms.DateTimeField(input_formats=datetime_input_formats,
                                         required=False)
    supposed_end = forms.DateTimeField(input_formats=datetime_input_formats,
                                       required=False)
    deadline = forms.DateTimeField(input_formats=datetime_input_formats,
                                   required=False)

    project = forms.IntegerField(label='Project', required=False)

    plan_minute = forms.IntegerField(label='Minute', required=False)
    plan_hour = forms.IntegerField(label='Hour', required=False)
    plan_day = forms.IntegerField(label='Day', required=False)
    plan_month = forms.IntegerField(label='Month', required=False)
    plan_year = forms.IntegerField(label='Year', required=False)

    def string_time_to_datetime(self, string_time):
        '''Converts string representation of time to datetime object
        String representation is a string in correct format (see datetime_input_formats)
        '''

        for format in self.datetime_input_formats:
            datetime_object = datetime.datetime.strptime(string_time, format)
            if datetime_object is not None:
                return datetime_object

class TaskSearchForm(TaskForm):
    status_choices = [('overdue', 'overude'), ('pending', 'pending'), 
                        ('active', 'active'), ('completed', 'completed')]

    title = forms.CharField(label='Title', max_length=256, required=False)

    priority = forms.MultipleChoiceField(choices=TaskForm.priority_choices,
                                required=False)
    status = forms.MultipleChoiceField(choices=status_choices,
                                required=False)

    timeless = forms.ChoiceField(choices=[('true', 'true'), ('false', 'false')], required=False)

class ProjectForm(forms.Form):
    name = forms.CharField(label='Name', max_length=256, required=True)