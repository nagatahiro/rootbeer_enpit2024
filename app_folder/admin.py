from django.contrib import admin
from .models import Purchase,CustomGroup,PaymentDetail

admin.site.register(Purchase)
admin.site.register(CustomGroup)
admin.site.register(PaymentDetail)