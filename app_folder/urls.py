from django.urls import path
from . import views

app_name = "app_folder"  # 名前空間を正しく設定

urlpatterns = [
    path('', views.TopView.as_view(), name='top'),
    path('home/', views.HomeView.as_view(), name='home'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('signup/', views.SignUp.as_view(), name='signup'),
    path('create-group/', views.CreateGroupView.as_view(), name='create_group'),
    path('home/<int:group_id>/', views.GroupDetailView.as_view(), name='group_detail'),
    path('add-friend/', views.AddFriendPageView.as_view(), name='add_friend'),  # フレンド追加用のURL
]
