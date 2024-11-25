from django.shortcuts import render
from django.views import View  
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
from .forms import SignUpForm
from django.contrib.auth import login
from django.urls import reverse

from . import forms
  
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

from django.shortcuts import render
from django.views import View  
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from .forms import DutchTreatForm

class DutchTreatView(LoginRequiredMixin, View):
    """割り勘計算ページ"""

    def get(self, request, *args, **kwargs):
        form = DutchTreatForm()
        return render(request, 'app_folder/dutch_treat.html', {'form': form})

    def post(self, request, *args, **kwargs):
        form = DutchTreatForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            item_name = form.cleaned_data['item_name']
            people = form.cleaned_data['people']

            # 割り勘計算
            share = amount // people
            remainder = amount % people

            context = {
                'form': form,
                'item_name': item_name,
                'amount': amount,
                'people': people,
                'share': share,
                'remainder': remainder,
            }
            return render(request, 'app_folder/dutch_treat.html', context)

        return render(request, 'app_folder/dutch_treat.html', {'form': form})


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