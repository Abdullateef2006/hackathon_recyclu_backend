# class ValidateUserCoinsView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request, user_id):
#         company = request.user

#         if not hasattr(company, 'company_profile') or not company.company_profile.is_verified:
#             return Response({'error': 'Only verified companies can validate coins'}, status=403)

#         try:
#             user = User.objects.get(id=user_id)
#         except User.DoesNotExist:
#             return Response({'error': 'User not found'}, status=404)

#         if user.company_profile is not None:
#             return Response({'error': 'User is already attached to a company'}, status=400)

#         if user.coins <= 0:
#             return Response({'error': 'No invalid coins to validate'}, status=400)

#         # Transfer all coins to valid_coins
#         validated_amount = user.coins
#         user.valid_coins += validated_amount
#         user.coins = 0
#         user.save()

#         return Response({
#             'message': f'{validated_amount} coins validated for user {user.username}',
#             'new_valid_coins': user.valid_coins
#         })


# class ValidateUserCoinsView(APIView):
#     permission_classes = [IsAuthenticated]
#     authentication_classes = [JWTAuthentication]


#     def post(self, request, user_id):
#         company = request.user

#         # Make sure the request user has a verified company profile
#         if not hasattr(company, 'company_profile') or not company.company_profile.is_verified:
#             return Response({'error': 'Only verified companies can validate coins'}, status=403)

#         try:
#             user = User.objects.get(id=user_id)
#         except User.DoesNotExist:
#             return Response({'error': 'User not found'}, status=404)

#         # 🔐 Check if user has a company_profile (to make sure they are not attached to a company)
#         if hasattr(user, 'company_profile'):
#             return Response({'error': 'User is already attached to a company'}, status=400)

#         if user.coins <= 0:
#             return Response({'error': 'No  coins to validate'}, status=400)

#         # Transfer invalid coins → valid coins
#         validated_amount = user.coins
#         user.valid_coins += validated_amount
#         user.coins = 0
#         user.save()

#         return Response({
#             'message': f'{validated_amount} coins validated for user {user.username}',
#             'new_valid_coins': user.valid_coins
#         })


# from rest_framework.views import APIView
# from rest_framework.response import Response
# from django.db.models import Sum, Case, When, IntegerField
# from .models import User, CoinTransaction

# class WeeklyLeaderboardView(APIView):
#     def get(self, request):
#         # Annotate users with the total coins earned from all transaction types
#         top_users = (
#             User.objects.annotate(
#                 total_earned=Sum(
#                     Case(
#                         When(coin_transactions__amount__isnull=False, then='coin_transactions__amount'),
#                         default=0,
#                         output_field=IntegerField()
#                     )
#                 )
#             )
#             .order_by('-total_earned')  # Order by total coins earned in descending order
#             .distinct()  # Ensure no duplicates
#         )

#         # Prepare the data to return in the response
#         data = [
#             {
#                 'username': user.username,
#                 'total_earned': user.total_earned or 0
#             }
#             for user in top_users
#         ]
        
#         # Return the response with the top users and their total coins earned
#         return Response(data)



# class RegisterView(APIView):
#     permission_classes = [AllowAny]  # No authentication required

#     serializer_class = RegisterSerializer
#     def post(self, request):
#         serializer = RegisterSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         user = serializer.save()

#         refresh = RefreshToken.for_user(user)
#         return Response({
#             "user": {
#                 "username": user.username,
#                 "email": user.email,
#                 "coins": user.coins,
#                 "referral_code": user.referral_code,
#             },
#             "access": str(refresh.access_token),
#             "refresh": str(refresh),
#         }, status=status.HTTP_201_CREATED)


# class WithdrawCoinView(APIView):
#     def post(self, request):
#         user = request.user
#         pin = request.data.get('pin')
#         description = request.data.get('description')

#         amount = int(request.data.get('amount', 0))

#         # Check if PIN is empty
#         if not pin:
#             return Response({'error': 'PIN is required'}, status=status.HTTP_400_BAD_REQUEST)

#         # Check if the provided PIN is valid
#         if not user.check_pin(pin):
#             return Response({'error': 'Invalid PIN'}, status=status.HTTP_400_BAD_REQUEST)

#         # Check if the user has enough coins for the withdrawal
#         if user.coins < amount:
#             return Response({'error': 'Insufficient coins'}, status=status.HTTP_400_BAD_REQUEST)

#         # Subtract the amount from the user's coin balance
#         user.coins -= amount
#         user.save()

#         # Create a coin transaction for the withdrawal
#         CoinTransaction.objects.create(
#             user=user,
#             amount=-amount,
#             transaction_type='withdrawal'
#         )

#         return Response({'message': f'{amount} coins withdrawn successfully', 'balance' : user.coins, "description" : description}, status=200)