from django.urls import path
from . import views
from .views import TopView
from django.contrib.auth.views import LogoutView
from .views import edit_group,join_group

app_name = "app_folder"  

urlpatterns = [

    path('top/', views.TopView.as_view(), name='top'),
    path("home/", views.HomeView.as_view(), name="home"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path('signup/', views.SignUp.as_view(), name='signup'),
    path('create-group/', views.CreateGroupView.as_view(), name='create_group'),  # グループ作成ページ
    path('home/<int:group_id>/', views.GroupDetailView.as_view(), name='group_detail'),  # グループ詳細ページ
    path('edit-group/<int:group_id>/', views.EditGroupView.as_view(), name='edit_group'),
    path('photograph/', views.PhotographView.as_view(), name='photograph'),
    path('edit-group/<int:id>/', edit_group, name='edit_group'),
    path('home/<int:group_id>/photo', views.ShootingRegistration.as_view(), name='shooting_registration'), #撮影ページ
    path('home/<int:group_id>/camera', views.CameraView.as_view(), name='camera'),#カメラ機能 1/7
    path('join_group/<str:token>/', join_group, name='join_group'),
    path('information/', views.HowToView.as_view(), name='howtouse'),
]

