"""
URL configuration for app_config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import include

# URLの全体設計
urlpatterns = [
    # 今回作成するアプリ「app_folder」にアクセスするURL
    path('app_folder/', include('app_folder.urls')),
    # 何もURLを指定しない場合（app_config/views.pyで、自動的に「app_folder」にアクセスするよう設定済み）
    path('', views.index, name='index'),
    # 管理サイトにアクセスするURL
    path('admin/', admin.site.urls),
]

# メディアファイル公開用のURL設定
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += staticfiles_urlpatterns()