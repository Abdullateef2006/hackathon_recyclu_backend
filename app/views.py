from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics, parsers
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import *
from .models import *
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import AllowAny, IsAuthenticated
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from drf_spectacular.utils import extend_schema, OpenApiExample,OpenApiResponse
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .serializers import CustomTokenObtainPairSerializer
from django.contrib.auth import get_user_model
from .models import RecyclableUpload, CoinTransaction
from .serializers import RecyclableUploadSerializer
import nyckel
from django.conf import settings

from .serializers import CompanyProfileSerializer
from .models import CompanyProfile
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import api_view






User = get_user_model()

class RegisterView(APIView):
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    def post(self, request):
        data = request.data.copy()  # Make it mutable
        referral_code = request.query_params.get("referral_code")

        if referral_code:
            data['referral_code'] = referral_code  # Inject referral code into serializer data

        serializer = RegisterSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)
        return Response({
            "user": {
                "username": user.username,
                "email": user.email,
                "coins": user.coins,
                "referral_code": user.referral_code,
            },
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }, status=status.HTTP_201_CREATED)




class CountryListView(generics.ListAPIView):
    queryset = Country.objects.all()
    serializer_class = CountrySerializer



class CoinTransactionHistoryView(generics.ListAPIView):
    serializer_class = CoinTransactionSerializer
    authentication_classes = [JWTAuthentication]

    

    def get_queryset(self):
        return CoinTransaction.objects.filter(user=self.request.user).order_by('-timestamp')





class WithdrawCoinView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    
    @extend_schema(
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "pin": {"type": "string", "example": "1234"},
                    "description": {"type": "string", "example": "Need cash"},
                    "amount": {"type": "integer", "example": 500},
                },
                "required": ["pin", "amount"]
            }
            ,'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'pin': {'type': 'string', 'example': '1234'},
                    'amount': {'type': 'integer', 'example': 500},
                    'description': {'type': 'string', 'example': 'Withdrawing for shopping'}
                },
                'required': ['pin', 'amount']
            }
        },
        responses={
            200: OpenApiExample(
                'Successful Withdrawal',
                summary='Success response',
                value={
                    'message': 'Withdrawal of 500 coins successful',
                    'remaining_valid_coins': 1000,
                    'description': 'Need cash'
                },
                response_only=True,
                status_codes=["200"]
            ),
            400: OpenApiExample(
                'Invalid PIN',
                summary='Error response',
                value={"error": "Invalid PIN"},
                response_only=True,
                status_codes=["400"]
            ),
        },
        description="Withdraw coins by providing your PIN and amount."
    )

    def post(self, request):
        user = request.user
        pin = request.data.get('pin')
        description = request.data.get('description', '')
        amount = int(request.data.get('amount', 0))
        
        if not pin or len(pin) < 4:
            return Response({'error': 'PIN is required and must be at least 4 digits'}, status=400)

        if not user.check_pin(pin):
            return Response({'error': 'Invalid PIN'}, status=400)

        if amount <= 0:
            return Response({'error': 'Invalid amount'}, status=400)

        if user.valid_coins < amount:
            return Response({'error': 'Insufficient valid coins'}, status=400)

        user.valid_coins -= amount
        user.save()
        
        send_mail(
            subject='[Withdrawal Request] - User Needs Manual Credit',
            message=f"User '{user.username}' ({user.email}) requested a withdrawal of {amount} coins.\n\n"
                    f"New Valid Coin Balance: {user.valid_coins}\nPlease credit their account manually. \n\n bank_name: {user.bank_name} \naccount_number: {user.account_number}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.ADMIN_NOTIFICATION_EMAIL],
            fail_silently=False,
        )

        CoinTransaction.objects.create(
            user=user,
            amount=-amount,
            transaction_type='withdrawal',
            description=description
        )
        
        
        notification = Notification.objects.create(
        user=user,
        message=f"You have successfully made a withdrawal of {amount} coins ",
        notification_type='withdrawal'

        )

    # Send it over WebSocket
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"user_{user.id}",  # Group name
            {
                'type': 'send_notification',
                'message': notification.message,
                'created_at': str(notification.created_at)
            }
        )


        return Response({
            'message': f'Withdrawal of {amount} coins successful',
            'remaining_valid_coins': user.valid_coins, 
            'description': description
        })





class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]


    def get(self, request):
        serializer = UserProfileSerializer(request.user, context={'request': request})
        return Response(serializer.data, status=200)


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer





class LeaderboardView(APIView):
    def get(self, request):
        top_users = User.objects.all().order_by('-coins')[:10]
        data = [
            {
                "username": user.username,
                "email": user.email,
                "coins": user.coins,
                "referral_code": user.referral_code
            }
            for user in top_users
        ]
        return Response(data, status=status.HTTP_200_OK)



# Nyckel credentials
NYCKEL_CREDENTIALS = nyckel.Credentials(
    "83qxpxmije8qtyh44rdjz7u7wxutzau3", 
    "9c7kedxfim5s366l87wpqb219j1s2ti9k4hhrxpquy0d214pq9krd4dx95avb4cp"
)
NYCKEL_FUNCTION_ID = "recycling-identifier"

# Labels considered recyclable
RECYCLABLE_LABELS = ["Plastic Bottle", "Paper", "Metal Can", "Glass", "Carton"]


class CheckRecyclableFromUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]
    authentication_classes = [JWTAuthentication]

    @extend_schema(
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'image': {
                        'type': 'string',
                        'format': 'binary',
                        'description': 'Upload image to check if recyclable'
                    }
                },
                'required': ['image']
            }
        },
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'recyclable': {'type': 'boolean'},
                    'label': {'type': 'string'},
                    'confidence': {'type': 'number', 'format': 'float'},
                    'coins_added': {'type': 'integer'},
                    'new_balance': {'type': 'integer'},
                    'image_url': {'type': 'string', 'format': 'uri'}
                }
            },
            400: {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            },
            500: {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            },
        },
        description="Upload an image to check if it's recyclable using Nyckel AI. If recyclable, user earns 10 coins."
    )

    def post(self, request):
        file = request.FILES.get("image")
        if not file:
            return Response({"error": "Image file is required"}, status=400)

        # ✅ Save image using Cloudinary-backed model storage
        uploaded = RecyclableUpload.objects.create(user=request.user, image=file)
        image_url = uploaded.image.url  # Cloudinary returns public URL directly

        # 🔍 Call Nyckel API to classify image
        try:
            result = nyckel.invoke(NYCKEL_FUNCTION_ID, image_url, NYCKEL_CREDENTIALS)
        except Exception as e:
            return Response({"error": f"Nyckel error: {str(e)}"}, status=500)

        label = result.get("labelName")
        confidence = result.get("confidence", 0)

        # Check for recyclable or "(Recyclable)" in label
        is_recyclable = (
            label and (
                label in RECYCLABLE_LABELS or 
                "(Recyclable)" in label
            )
        ) and confidence >= 0.80

        if is_recyclable:
            request.user.coins += 10
            request.user.save()

            CoinTransaction.objects.create(
                user=request.user,
                amount=10,
                transaction_type='recycling_reward',
                description=f"Recycled {label} and earned 10 coins"
            )

            return Response({
                "recyclable": True,
                "label": label,
                "confidence": confidence,
                "coins_added": 10,
                "new_balance": request.user.coins,
                "image_url": image_url,
            }, status=200)

        # Not recyclable
        return Response({
            "recyclable": False,
            "label": label,
            "confidence": confidence,
            "image_url": image_url
        }, status=200)




class CompanyRegistrationView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    parser_classes = [parsers.MultiPartParser, parsers.FormParser]  # ✅ allow file uploads
    serializer_class = CompanyProfileSerializer

    @extend_schema(
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'company_name': {'type': 'string'},
                    'registration_number': {'type': 'string'},
                    'recycling_license': {
                        'type': 'string',
                        'format': 'binary',
                        'description': 'Upload your recycling license file'
                    }
                },
                'required': ['company_name', 'registration_number', 'recycling_license']
            }
        },
        responses={
            201: OpenApiResponse(description="Company registered successfully. Awaiting admin approval."),
            400: OpenApiResponse(description="You already registered a company or invalid data."),
        },
        description="Register your company and upload a recycling license (file)."
    )
    def post(self, request):
        if hasattr(request.user, 'company_profile'):
            return Response({"detail": "You already registered a company."}, status=400)

        serializer = CompanyProfileSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response({"detail": "Company registered successfully. Awaiting admin approval."}, status=201)
        return Response(serializer.errors, status=400)


class UnattachedUserListView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]


    def get(self, request):
        user = request.user
        if not hasattr(user, 'company_profile') or not user.company_profile.is_verified:
            return Response({'error': 'Not a verified company'}, status=403)

        users_without_company = User.objects.filter(company_profile__isnull=True)
        serializer = UserSerializer(users_without_company, many=True)
        return Response(serializer.data)




from rest_framework.parsers import JSONParser



class ValidateUserCoinsView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    parser_classes = [MultiPartParser]  # 👈 Accept form-data

    @extend_schema(
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'validation_type': {
                        'type': 'string',
                        'enum': ['pickup', 'dropoff'],
                        'description': 'pickup = 85%, dropoff = 100%'
                    }
                },
                'required': ['validation_type']
            }
        },
        responses={
            200: {'type': 'object'},
            400: {'type': 'object'},
            403: {'type': 'object'},
            404: {'type': 'object'},
        }
    )


    def post(self, request, user_id):
        company = request.user
        validation_type = request.data.get('validation_type')  # 'dropoff' or 'pickup'

        if validation_type not in ['dropoff', 'pickup']:
            return Response({'error': "validation_type must be either 'dropoff' or 'pickup'"}, status=400)

        # ✅ Check if request user is a verified company
        if not hasattr(company, 'company_profile') or not company.company_profile.is_verified:
            return Response({'error': 'Only verified companies can validate coins'}, status=403)

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)

        # 🔐 Check if user is not a company
        if hasattr(user, 'company_profile'):
            return Response({'error': 'User is already attached to a company'}, status=400)

        if user.coins <= 0:
            return Response({'error': 'No coins to validate'}, status=400)

        original_coins = user.coins

        # 💡 Process coin validation logic
        if validation_type == 'pickup':
            validated_amount = int(original_coins * 0.85)
        elif validation_type == 'dropoff':
            validated_amount = original_coins

        user.valid_coins += validated_amount
        user.coins = 0  # Always reset invalid coins
        user.save()
        
        
        notification = Notification.objects.create(
        user=user,
        message=f"You have successfully validated {validated_amount} coins via {validation_type}.",
        notification_type=validation_type

        )

    # Send it over WebSocket
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"user_{user.id}",  # Group name
            {
                'type': 'send_notification',
                'message': notification.message,
                'created_at': str(notification.created_at)
            }
        )
        
        
        

        return Response({
            'message': f'{validated_amount} coins validated for user {user.username} via {validation_type}',
            'new_valid_coins': user.valid_coins,
            'coins': user.coins,
            'validation_type': validation_type
        })



from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .serializers import ProfileSerializer

class ProfileView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]


    def get(self, request):
        # Retrieve the current user's profile
        user = request.user
        serializer = ProfileSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request):
        # Update the user's profile (e.g., pin, bank details)
        user = request.user
        serializer = ProfileSerializer(user, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@api_view(['POST'])
def mark_as_read(request, notification_id):
    try:
        notification = Notification.objects.get(id=notification_id, user=request.user)
        notification.is_read = True
        notification.save()
        return Response({'status': 'Notification marked as read'})
    except Notification.DoesNotExist:
        return Response({'error': 'Notification not found'}, status=404)




class NotificationListView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        user = request.user
        is_read_filter = request.query_params.get('is_read')

        # Optional: filter by read status
        if is_read_filter is not None:
            notifications = user.notifications.filter(is_read=(is_read_filter.lower() == 'true'))
        else:
            notifications = user.notifications.all()

        notification_data = [
            {
                'id': n.id,
                'message': n.message,
                'is_read': n.is_read,
                'created_at': n.created_at.isoformat(),
                'notification_type': n.notification_type
            }
            for n in notifications.order_by('-created_at')
        ]

        return Response({'notifications': notification_data})




class WebSocketInfoView(APIView):
    @extend_schema(
        description="""
            **WebSocket Notification URL**

            Connect using a WebSocket client (JavaScript, React, React Native, etc.) to:

            `ws://yourdomain.com/ws/notifications/?token=<JWT_TOKEN>`

            Replace `<JWT_TOKEN>` with your valid JWT access token.

            **Example:**
            ```javascript
            const ws = new WebSocket("ws://yourdomain.com/ws/notifications/?token=YOUR_JWT_TOKEN");
            ```
        """,
        responses={200: OpenApiResponse(description="WebSocket URL info")}
    )
    def get(self, request):
        return Response({
            "websocket_url": "ws://yourdomain.com/ws/notifications/?token=<JWT_TOKEN>"
        })



class CompanyRegisterView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'username': {'type': 'string'},
                    'email': {'type': 'string'},
                    'password': {'type': 'string', 'format': 'password'},
                    'company_name': {'type': 'string'},
                    'registration_number': {'type': 'string'},
                    'recycling_license': {'type': 'string', 'format': 'binary'},
                },
                'required': ['username', 'email', 'password', 'company_name', 'registration_number', 'recycling_license']
            }
        },
        responses={201: OpenApiResponse(description="Company registered successfully")}
    )
    def post(self, request):
        user_data = {
            'username': request.data.get('username'),
            'email': request.data.get('email'),
            'password': request.data.get('password'),
        }
        user_serializer = RegisterSerializer(data=user_data)
        user_serializer.is_valid(raise_exception=True)
        user = user_serializer.save()

        company_data = {
            'user': user.id,
            'company_name': request.data.get('company_name'),
            'registration_number': request.data.get('registration_number'),
            'recycling_license': request.data.get('recycling_license'),
        }
        company_serializer = CompanyProfileSerializer(data=company_data)
        company_serializer.is_valid(raise_exception=True)
        company_serializer.save(user=user)

        refresh = RefreshToken.for_user(user)
        return Response({
            'message': 'Company registered successfully. Awaiting admin approval.',
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }, status=201)




class CustomLoginView(TokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class = MyTokenObtainPairSerializer






from .serializers import CompanyLoginSerializer


class CompanyLoginView(APIView):
    permission_classes = [AllowAny]
    serializer_class = CompanyLoginSerializer


    def post(self, request):
        serializer = CompanyLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=200)
