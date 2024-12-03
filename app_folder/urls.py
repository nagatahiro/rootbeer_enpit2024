from django.urls import path
from . import views
from .views import TopView
from django.contrib.auth.views import LogoutView

app_name = "app_folder"  # 名前空間を正しく設定

urlpatterns = [
    path('top/', TopView.as_view(), name='top'),  # Topページ
    path('logout/', LogoutView.as_view(next_page='app_folder:top'), name='logout'),  # ログアウト後にTopページにリダイレクト
    path('home/', views.HomeView.as_view(), name='home'),  # ホームページ
    path('login/', views.LoginView.as_view(), name='login'),  # ログインページ
    path('signup/', views.SignUp.as_view(), name='signup'),  # サインアップページ
    path('create-group/', views.CreateGroupView.as_view(), name='create_group'),  # グループ作成ページ
    path('home/<int:group_id>/', views.GroupDetailView.as_view(), name='group_detail'),  # グループ詳細ページ
    path('add-friend/', views.AddFriendPageView.as_view(), name='add_friend'),  # フレンド追加用のURL
    path('group/<int:group_id>/edit/', views.EditGroupView.as_view(), name='edit_group'),
    path('photograph/', views.PhotographView.as_view(), name='photograph'), #  撮影ページリンク
]
