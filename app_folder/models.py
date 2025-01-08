from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class CustomGroup(models.Model):
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_custom_groups')
    members = models.ManyToManyField(User, related_name='custom_group_members')
    regist_date = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Purchase(models.Model):
    group = models.ForeignKey(CustomGroup, on_delete=models.CASCADE, related_name='purchases', null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='purchases')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    store_name = models.CharField(max_length=255)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['group', 'date']),
        ]

    def __str__(self):
        return f"Group: {self.group.name} - {self.store_name} - ¥{self.total_amount}"
