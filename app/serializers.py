from rest_framework import serializers
from .models import *
from django.contrib.auth import get_user_model

User = get_user_model()

class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ['id', 'name']
        
        
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id","username", "email", "home_address","valid_coins", "coins", "country", ]
class RegisterSerializer(serializers.ModelSerializer):
    referral_code = serializers.CharField(required=False, allow_blank=True)
    # pin = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'country', 'referral_code','first_name', 'last_name', ]
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        referral_code = validated_data.pop('referral_code', None)
        referred_by = None

        if referral_code:
            referred_by = User.objects.filter(referral_code=referral_code).first()

        # raw_pin = validated_data.pop('pin')
        password = validated_data.pop('password')

        user = User(**validated_data)
        user.set_password(password)
        # user.set_pin(raw_pin)
        user.referred_by = referred_by
        user.save()

        if referred_by:
            referred_by.coins += 20
            referred_by.save()
            
              
            CoinTransaction.objects.create(
                user=referred_by,
                amount=20,
                transaction_type='referral_bonus',
                description=f"Referred {user.username} and received 20 coins"
            )

            user.coins += 20
            user.save()
            
            
            
            CoinTransaction.objects.create(
                user=user,
                amount=20,
                transaction_type='referral_bonus',
                description=f"Referred by {referred_by.username} and received 20 coins"
            )
            
            
            # 🔥 Indirect referral bonus (20% of 20 coins = 4 coins)
            grand_referrer = referred_by.referred_by
            if grand_referrer:
                bonus = int(0.2 * 20)
                grand_referrer.coins += bonus
                grand_referrer.save()

                CoinTransaction.objects.create(
                    user=grand_referrer,
                    amount=bonus,
                    transaction_type='indirect_referral_bonus',
                    description=f"Indirect referral via {referred_by.username} who referred {user.username} (earned {bonus} coins)"
                )
            
          
            
            
            

        return user


class CoinTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoinTransaction
        fields = ['id', 'amount', 'transaction_type', 'timestamp', "description"]

# serializers.py
from rest_framework import serializers

class ReferralSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class UserProfileSerializer(serializers.ModelSerializer):
    country = serializers.StringRelatedField()
    referred_by = ReferralSerializer(read_only=True, allow_null=True)
    referrals = ReferralSerializer(many=True, read_only=True)
    invite_link = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'referral_code', 'referred_by',
            'referrals', 'coins', 'country', 'bank_name',
            'account_number', 'date_joined', 'invite_link','valid_coins', 'first_name', 'last_name', 'profile_picture', 'home_address'
        ]

    def get_invite_link(self, obj):
        request = self.context.get('request')
        base_url = request.build_absolute_uri('/') if request else "https://example.com/"
        return f"{base_url}register/?referral_code={obj.referral_code}"

# serializers.py
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from django.contrib.auth import get_user_model

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user
        data.update({
            'username': user.username,
            'email': user.email,
            'coins': user.coins,
            'referral_code': user.referral_code
        })
        return data
# serializers.py
class RecyclableUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecyclableUpload
        fields = ['id', 'image', 'timestamp']


from rest_framework import serializers
from .models import CompanyProfile

class CompanyProfileSerializer(serializers.ModelSerializer):
    recycling_license = serializers.FileField(
        required=True,
        allow_empty_file=False,
        use_url=True
    )

    class Meta:
        model = CompanyProfile
        fields = [
            'company_name',
            'registration_number',
            'recycling_license',
        ]


from rest_framework import serializers

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['pin', 'bank_name', 'account_number','first_name', 'last_name','profile_picture', 'home_address', 'phone_number']

    def update(self, instance, validated_data):
        # Check if the pin is provided and update it
        pin = validated_data.get('pin', None)
        if pin:
            instance.set_pin(pin)

        # Update other fields
        instance.bank_name = validated_data.get('bank_name', instance.bank_name)
        instance.account_number = validated_data.get('account_number', instance.account_number)
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.profile_picture = validated_data.get('profile_picture', instance.profile_picture)
        instance.home_address = validated_data.get('home_address', instance.home_address)
        instance.phone_number = validated_data.get('phone_number', instance.phone_number)

        

        

        instance.save()
        return instance


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)

        user = self.user
        role = 'company' if hasattr(user, 'company_profile') else 'user'

        data.update({
            'username': user.username,
            'email': user.email,
            'role': role,
        })

        return data
# serializers.py

from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from .models import CompanyProfile


class CompanyLoginSerializer(serializers.Serializer):
    registration_number = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        reg_no = attrs.get("registration_number")
        password = attrs.get("password")

        try:
            company = CompanyProfile.objects.select_related('user').get(registration_number=reg_no)
        except CompanyProfile.DoesNotExist:
            raise serializers.ValidationError("Invalid registration number or password")

        user = company.user

        # ❌ Check password
        if not user.check_password(password):
            raise serializers.ValidationError("Invalid registration number or password")

        # ❌ Check verification status
        if not company.is_verified:
            raise serializers.ValidationError("Company is not verified yet")

        # ✅ All good → issue tokens
        refresh = RefreshToken.for_user(user)

        return {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'company_name': company.company_name,
            'registration_number': company.registration_number
        }
