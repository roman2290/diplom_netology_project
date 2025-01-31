from django import forms
from models import UserProfile


# Класс позволяет редактировать информацию о своем профиле
class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['avatar']