from django.db import models
from django.contrib.auth.models import User

class CustomGroup(models.Model):
    name = models.CharField(max_length=255, unique=True)  # グループ名
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_custom_groups')  # グループの所有者
    members = models.ManyToManyField(User, related_name='custom_group_members')  # グループのメンバー

    def __str__(self):
        return self.name
