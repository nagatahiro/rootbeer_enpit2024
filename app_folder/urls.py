from django.urls import path
from . import views
from .views import TopView
from django.contrib.auth.views import LogoutView
from .views import edit_group

app_name = "app_folder"  # 名前空間を正しく設定

urlpatterns = [
    path('top_page/', views.top_page, name='top_page'),
    path('top/', views.TopView.as_view(), name='top'),
    path("home/", views.HomeView.as_view(), name="home"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path('signup/', views.SignUp.as_view(), name='signup'),
    path('create-group/', views.CreateGroupView.as_view(), name='create_group'),  # グループ作成ページ
    path('home/<int:group_id>/', views.GroupDetailView.as_view(), name='group_detail'),  # グループ詳細ページ
    path('add-friend/', views.AddFriendPageView.as_view(), name='add_friend'),  # フレンド追加用のURL
    path('photograph/', views.PhotographView.as_view(), name='photograph'),
    path('edit-group/<int:id>/', edit_group, name='edit_group'),

]
