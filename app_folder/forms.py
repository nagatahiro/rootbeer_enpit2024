from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django import forms
from .models import Purchase, CustomGroup

class LoginForm(AuthenticationForm):
    """ログインフォーム"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"

class SignUpForm(UserCreationForm):

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'    


class SplitBillForm(forms.Form):
    selected_member = forms.ModelChoiceField(
        queryset=User.objects.all(),
        label="選択したメンバー",
        required=True,
        empty_label="メンバーを選んでください"
    )
    store_name = forms.CharField(
        max_length=100,
        label="店名",
        required=True
    )

    # グループIDはフォームに含めないが、初期値として渡すことができます
    group_id = forms.IntegerField(widget=forms.HiddenInput(), required=False)

    def __init__(self, *args, **kwargs):
        # group_idを初期値としてフォームに渡す
        group_id = kwargs.pop('group_id', None)
        super().__init__(*args, **kwargs)
        
        if group_id:
            self.fields['group_id'].initial = group_id

