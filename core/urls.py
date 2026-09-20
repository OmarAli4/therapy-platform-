from django.urls import path
from django.contrib.auth.views import LogoutView
from .views import (
    LandingView, CalmSpaceView, RegisterView, CustomLoginView,
    DashboardRouterView, ClientDashboardView, LogSomaticEnergyApiView,
    PostKindnessMessageApiView, LikeKindnessMessageApiView
)

urlpatterns = [
    path('', LandingView.as_view(), name='landing'),
    path('calm-space/', CalmSpaceView.as_view(), name='calm_space'),
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='landing'), name='logout'),
    path('dashboard/', DashboardRouterView.as_view(), name='dashboard'),
    path('dashboard/client/', ClientDashboardView.as_view(), name='client_dashboard'),
    path('api/log-energy/', LogSomaticEnergyApiView.as_view(), name='log_somatic_energy_api'),
    path('api/kindness-wall/post/', PostKindnessMessageApiView.as_view(), name='post_kindness_api'),
    path('api/kindness-wall/like/<int:pk>/', LikeKindnessMessageApiView.as_view(), name='like_kindness_api'),
]
