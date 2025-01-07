from django.db import models
from django.contrib.auth.models import User

class CustomGroup(models.Model):
    name = models.CharField(max_length=255)  # unique=True を削除
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_custom_groups')  # グループの所有者
    members = models.ManyToManyField(User, related_name='custom_group_members')  # グループのメンバー

    def __str__(self):
        return self.name


class Purchase(models.Model):
    purchaser = models.ForeignKey(User, on_delete=models.CASCADE, related_name="purchases")  # 購入者
    amount = models.DecimalField(max_digits=10, decimal_places=2)  # 金額
    date = models.DateField()  # 購入日
    group = models.ForeignKey(CustomGroup, on_delete=models.CASCADE, related_name="purchases", default=1)  # グループへの参照

    def __str__(self):
        return f"{self.purchaser.username} - ¥{self.amount} on {self.date} (Group: {self.group.name})"