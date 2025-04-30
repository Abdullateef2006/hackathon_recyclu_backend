from django.contrib import admin
from .models import  Country, CoinTransaction, CompanyProfile,UserManager, Notification, RecyclableUpload
from django.contrib.auth import get_user_model

User = get_user_model()
admin.site.register(User)
admin.site.register(Country)
admin.site.register(CoinTransaction)
admin.site.register(CompanyProfile)
admin.site.register(Notification)
admin.site.register(RecyclableUpload)




