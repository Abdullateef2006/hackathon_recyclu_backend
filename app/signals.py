from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import CompanyProfile

@receiver(post_save, sender=CompanyProfile)
def notify_admin_of_new_company(sender, instance, created, **kwargs):
    if created:
        send_mail(
            subject="New Recycling Company Registration",
            message=f"""
A new company has registered:

Company Name: {instance.company_name}
Email: {instance.user.email}
Registration Number: {instance.registration_number}
Recycling License: {instance.recycling_license.url if instance.recycling_license else 'Not provided'}
Login to admin panel to review and verify.
""",
            from_email=instance.user.email,
            recipient_list=[settings.ADMIN_NOTIFICATION_EMAIL],
        )
