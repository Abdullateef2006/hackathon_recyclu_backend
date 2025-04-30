from django.urls import path
from .views import *
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('api/auth/register-company/', CompanyRegisterView.as_view()),  # company
    path('api/auth/company-login/', CompanyLoginView.as_view(), name='company-login'),

    path('api/countries/', CountryListView.as_view(), name='countries'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/coin/history/', CoinTransactionHistoryView.as_view(), name='coin-history'),
    path('api/coin/withdraw/', WithdrawCoinView.as_view(), name='coin-withdraw'),
    # path('api/leaderboard/weekly/', WeeklyLeaderboardView.as_view(), name='weekly-leaderboard'),
    path('api/profile/', UserProfileView.as_view(), name='user-profile'),
    path('api/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('leaderboard/', LeaderboardView.as_view(), name='leaderboard'),
    path('check_recyclable_upload/', CheckRecyclableFromUploadView.as_view(), name='check-recyclable-upload'),
    # path("register_company/", CompanyRegistrationView.as_view(), name="register_company"),
    path('users_list/', UnattachedUserListView.as_view(), name='unattached-users'),
    path('users/validate_userCoins/<int:user_id>/', ValidateUserCoinsView.as_view(), name='validate-user-coins'),
    # path('coins/withdraw/', WithdrawCoinView.as_view(), name='withdraw-coins'),
    path('update_profile/', ProfileView.as_view(), name='profile'),
    path('notifications/', NotificationListView.as_view(), name='notification-list'),
    path('notifications_websocket/', WebSocketInfoView.as_view(), name='notifications_websocket'),



]
