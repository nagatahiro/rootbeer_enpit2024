from django.shortcuts import render
from django.views import View  
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
from .forms import SignUpForm
from django.contrib.auth import login
from django.urls import reverse
from django.core.files.base import ContentFile
from . import forms
from google.cloud import vision

import numpy as np
import cv2
import base64
from pytesseract import image_to_string
import os

class SampleView(View):  
	def get(self, request, *args, **kwargs):  
		return render(request, 'app_folder/top_page.html')
top_page = SampleView.as_view()




class TopView(TemplateView):
    template_name = "app_folder/top.html"

class HomeView(LoginRequiredMixin, TemplateView):
    template_name = "app_folder/home.html"

class LoginView(LoginView):
    """ログインページ"""
    form_class = forms.LoginForm
    template_name = "app_folder/login.html"

class LogoutView(LoginRequiredMixin, LogoutView):
    """ログアウトページ"""
    template_name = "app_folder/login.html"

class SignUp(CreateView):
    form_class = SignUpForm
    template_name = "app_folder/signup.html" 
    success_url = reverse_lazy('top')

    def form_valid(self, form):
        user = form.save() # formの情報を保存
        login(self.request, user) # 認証
        self.object = user 
        return HttpResponseRedirect(self.get_success_url()) # リダイレクト
    def get_success_url(self):
        # 成功後にリダイレクトする URL を指定
        return reverse('app_folder:home')

class PhotographView(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'app_folder/photograph.html')

    def post(self, request, *args, **kwargs):
        try:
            # リクエストから画像データを取得
            image_data = request.POST.get('image')
            if not image_data:
                return JsonResponse({'status': 'error', 'message': '画像データがありません。'})

            # Base64データをデコード
            _, encoded = image_data.split(",", 1)  # "data:image/jpeg;base64,..." 形式を分割
            image_bytes = base64.b64decode(encoded)

            # Google Cloud Vision API クライアントの初期化
            client = vision.ImageAnnotatorClient()

            # Vision API 用の画像オブジェクト作成
            image = vision.Image(content=image_bytes)

            # テキスト認識をリクエスト
            response = client.text_detection(image=image)

            # 抽出されたテキスト
            texts = response.text_annotations
            if texts:
                extracted_text = texts[0].description  # 最初のテキストが全文
            else:
                extracted_text = "テキストが検出されませんでした。"

            return JsonResponse({'status': 'success', 'extracted_text': extracted_text})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})