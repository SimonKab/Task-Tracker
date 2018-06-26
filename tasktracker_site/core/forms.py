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

    def string_time_to_datetime(self, string_time):
        '''Converts string representation of time to datetime object
        String representation is a string in correct format (see datetime_input_formats)
        '''

        for format in self.datetime_input_formats:
            datetime_object = datetime.datetime.strptime(string_time, format)
            if datetime_object is not None:
                return datetime_object

class ProjectForm(forms.Form):
    name = forms.CharField(label='Name', max_length=256, required=True)