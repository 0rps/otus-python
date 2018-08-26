from django import forms


class QuestionForm(forms.Form):

    title = forms.CharField(label='Question',
                            min_length=4,
                            max_length=128,
                            widget=forms.TextInput(attrs={'class': 'form-control',
                                                          'placeholder': 'Question'}))

    body = forms.CharField(label='Description',
                           widget=forms.Textarea(attrs={'class': 'form-control',
                                                        'placeholder': 'Description'}))

    tags = forms.CharField(label='Tags', required=False,
                           widget=forms.TextInput(attrs={'class': 'form-control',
                                                         'placeholder': 'tag_1,tag_2,tag_3'}))

    def clean(self):
        cleaned_data = super().clean()

        if 'tags' in cleaned_data:
            tags = cleaned_data['tags'].split(',')
            tags = [tag.strip() for tag in tags if len(tag.strip()) > 0]
            if len(tags) > 3:
                self.add_error('tags', 'Maximum is 3 tags')
            else:
                cleaned_data['tags'] = tags
        else:
            raise Exception('Empty tags')
        return cleaned_data


class AnswerForm(forms.Form):

    body = forms.CharField(label='Description', min_length=4,
                           widget=forms.Textarea(attrs={'class': 'form-control',
                                                        'placeholder': 'Your answer'}))
