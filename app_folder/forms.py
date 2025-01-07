from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django import forms

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

class SplitBillForm(forms.Form):#割り勘用のファイル
    amount = forms.DecimalField(label="合計金額", max_digits=10, decimal_places=2)
    members_count = forms.IntegerField(label="人数", min_value=1)

#追加↓
from .models import Purchase, CustomGroup

class PurchaseForm(forms.ModelForm):
    class Meta:
        model = Purchase
        fields = ['amount', 'date', 'group']
        labels = {
            'amount': '金額',
            'date': '購入日',
            'group': 'グループ',
        }
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')  # 現在のユーザーを取得
        super().__init__(*args, **kwargs)
        # 現在のユーザーが所属しているグループのみを選択肢に表示
        self.fields['group'].queryset = CustomGroup.objects.filter(members=user)