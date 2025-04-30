from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
import uuid

from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings

class Country(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class UserManager(BaseUserManager):
    def create_user(self, email, username, password=None, **extra_fields):
        if not email:
            raise ValueError("Users must have an email")
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        if 'pin' in extra_fields:
            user.set_pin(extra_fields['pin'])
        user.save()
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, username, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    coins = models.IntegerField(default=0)
    valid_coins = models.IntegerField(default=0)
    first_name = models.CharField(max_length=100, default="Unknown")
    last_name = models.CharField(max_length=100, default="Unknown")
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    


    referral_code = models.CharField(max_length=10, unique=True, blank=True)
    referred_by = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="referrals")

    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True)
    bank_name = models.CharField(max_length=100, blank=True)
    account_number = models.CharField(max_length=20, blank=True)
    pin = models.CharField(max_length=128)  # Hashed like password
    home_address = models.TextField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True)


    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)


    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        if not self.referral_code:
            self.referral_code = str(uuid.uuid4())[:10].upper()
        super().save(*args, **kwargs)

    def set_pin(self, raw_pin):
        from django.contrib.auth.hashers import make_password
        self.pin = make_password(raw_pin)

    def check_pin(self, raw_pin):
        from django.contrib.auth.hashers import check_password
        return check_password(raw_pin, self.pin)


class CoinTransaction(models.Model):
    TRANSACTION_TYPE = (
        ('referral_bonus', 'Referral Bonus'),
        ('withdrawal', 'Withdrawal'),
        ('recycling_reward', 'Recycling Reward'), 
        ('indirect_referral_bonus', 'indirect referral bonus'), 


    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='coin_transactions')
    amount = models.IntegerField()
    transaction_type = models.CharField(max_length=50, choices=TRANSACTION_TYPE)
    description = models.CharField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.transaction_type} - {self.amount}"
from django.db import models
from django.conf import settings
from cloudinary.models import CloudinaryField


class RecyclableUpload(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    image = CloudinaryField('image')  # 👈 this is the key change!
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.image.url}"

    def get_image_url(self):
        if self.image and hasattr(self.image, 'url'):
            return self.image.url
        return None
from django.db import models
from django.contrib.auth.models import User

class CompanyProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='company_profile')
    company_name = models.CharField(max_length=255)
    registration_number = models.CharField(max_length=100, unique=True)
    recycling_license = models.FileField(upload_to='licenses/')
    is_verified = models.BooleanField(default=False)  # Admin will verify this
    registered_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.company_name
    
    
    def save(self, *args, **kwargs):
        # Detect when `is_verified` was changed from False to True
        is_newly_verified = False
        if self.pk:
            old = CompanyProfile.objects.get(pk=self.pk)
            if not old.is_verified and self.is_verified:
                is_newly_verified = True

        super().save(*args, **kwargs)

        if is_newly_verified:
            # Send verification email
            subject = "✅ Company Verification Successful"
            message = f"Dear {self.user.username},\n\nYour company '{self.company_name}' has been successfully verified.\n\nYou can now access all features reserved for verified recyclers.\n\nThank you for being part of the mission to recycle!"
            from_email = settings.DEFAULT_FROM_EMAIL
            recipient_list = [self.user.email]

            send_mail(subject, message, from_email, recipient_list)



class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    notification_type = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.user.username} - {self.message}"


