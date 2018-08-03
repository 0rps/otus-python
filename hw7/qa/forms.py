from django import forms


class QuestionForm(forms.Form):

    title = forms.CharField(label='Question',
                            max_length=128,
                            widget=forms.TextInput(attrs={'class': 'form-control',
                                                          'placeholder': 'Question'}))

    body = forms.CharField(label='Description',
                           widget=forms.Textarea(attrs={'class': 'form-control',
                                                        'placeholder': 'Description'}))

    tags = forms.CharField(label='Tags',
                           widget=forms.CharField(attrs={'class': 'form-control',
                                                         'placeholder': 'Question'}))


class AnswerForm(forms.Form):

    body = forms.CharField(label='Description',
                           widget=forms.Textarea(attrs={'class': 'form-control',
                                                        'placeholder': 'Answer'}))
