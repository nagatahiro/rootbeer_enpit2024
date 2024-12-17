from django import template
from django.contrib.auth.models import User

register = template.Library()

@register.filter 
def get_user_username(user_id):
    """ユーザーIDからユーザー名を取得するフィルタ"""
    try:
       return User.objects.get (id=user_id).username
    except User.DoesNotExist:
       return "不明なユーザー"