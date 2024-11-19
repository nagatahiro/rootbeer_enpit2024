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

class Photograph(View):
    """撮影ページ + 文字抽出機能"""

    def get(self, request, *args, **kwargs):
        return render(request, 'app_folder/photograph.html')

    def post(self, request, *args, **kwargs):
        os.environ['TESSDATA_PREFIX'] = '/opt/homebrew/share/'

        image_data = request.POST.get('image')
        if not image_data:
            return JsonResponse({'status': 'error', 'message': 'No image data provided'})

        format, imgstr = image_data.split(';base64,')
        img_data = ContentFile(base64.b64decode(imgstr), name='uploaded.jpg')

        nparr = np.frombuffer(img_data.read(), np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (5, 5), 0)
        _, gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        cv2.imwrite('debug_image.jpg', gray)  # デバッグ用に保存

        try:
            text = image_to_string(gray, lang='jpn', config='--psm 6 --tessdata-dir /opt/homebrew/share/tessdata')
            print(f"OCR出力: {text}")  # デバッグ出力
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

        return JsonResponse({'status': 'success', 'extracted_text': text})