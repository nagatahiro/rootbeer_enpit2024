from django.contrib import admin
from .models import Purchase

@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('purchaser', 'amount', 'date')

    # データの追加や編集を禁止
    def has_add_permission(self, request):
        return False  # 追加を禁止

    def has_change_permission(self, request, obj=None):
        return False  # 編集を禁止

    def has_delete_permission(self, request, obj=None):
        return False  # 削除を禁止
