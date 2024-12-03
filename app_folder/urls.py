from django.urls import path
from . import views

app_name = 'app_folder'
urlpatterns = [
    path('top_page/', views.top_page, name='top_page'),
    path('top/', views.TopView.as_view(), name='top'),
    path("home/", views.HomeView.as_view(), name="home"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path('signup/', views.SignUp.as_view(), name='signup'),
    path('photograph/', views.PhotographView.as_view(), name='photograph'),
]
