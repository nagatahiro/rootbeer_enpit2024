from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class CustomGroup(models.Model):
    name = models.CharField(max_length=255)  
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_custom_groups')  # グループの所有者
    members = models.ManyToManyField(User, related_name='custom_group_members')  # グループのメンバー
    regist_date = models.DateTimeField(default=timezone.now)  # 現在時刻をデフォルト値として設定
    created_at = models.DateTimeField(auto_now_add=True)  # default=timezone.now を削除

    def __str__(self):
        return self.name
