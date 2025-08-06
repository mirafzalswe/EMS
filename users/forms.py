from django.contrib.auth.forms import PasswordChangeForm
from django import forms
from users.models import User

class StudentChangePasswordForm(PasswordChangeForm):
    class Meta:
        model = User
        fields = ['old_password', 'new_password1', 'new_password2']
    
    def clean_new_password2(self):
        new_password2 = self.cleaned_data.get('new_password2')
        if not new_password2:
            raise forms.ValidationError('New password confirmation is required.')
        return new_password2


class StudentProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name','last_name', 'email', 'phone']
    
    