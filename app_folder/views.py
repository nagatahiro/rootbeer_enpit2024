from django.shortcuts import render, redirect
from django.views import View
from django.views.generic import TemplateView  
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy, reverse
from django.views.generic.edit import CreateView
from django.contrib.auth import login
from .forms import SignUpForm
from django.contrib import messages
from django.contrib.auth.models import Group

from . import forms

class TopView(TemplateView):  # TopView の定義
    template_name = "app_folder/top.html"

class HomeView(LoginRequiredMixin, TemplateView):
    template_name = "app_folder/home.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        groups = self.request.user.groups.all()
        orgs = [group.org for group in groups]
        context['orgs'] = orgs
        return context

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
    success_url = reverse_lazy('app_folder:home')

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        self.object = user
        return HttpResponseRedirect(self.get_success_url())

class CreateGroupView(LoginRequiredMixin, TemplateView):
    """グループ作成ページ"""
    template_name = "app_folder/create_group.html"

    def post(self, request, *args, **kwargs):
        group_name = request.POST.get('group_name')
        invited_friends = request.POST.getlist('friends')  # 選択されたフレンドのIDリスト
        if group_name:
            group, created = Group.objects.get_or_create(name=group_name)
            # 仮のフレンド処理（選択されたフレンドIDを表示）
            print(f"グループ '{group_name}' に招待されたフレンド: {invited_friends}")
            messages.success(request, f"グループ '{group_name}' を作成しました。")
        return HttpResponseRedirect(reverse('app_folder:home')) # ホーム画面にリダイレクト


class AddFriendPageView(LoginRequiredMixin, TemplateView):
    template_name = "app_folder/add_friend.html"

    def post(self, request, *args, **kwargs):
        # フレンド追加処理
        friend_name = request.POST.get('friend_name')
        print(f"フレンド '{friend_name}' を追加しました。")
        return redirect('app_folder:home')
    
class GroupDetailView(LoginRequiredMixin, TemplateView):
    """グループ詳細ページ"""
    template_name = "app_folder/group_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group_id = self.kwargs.get('group_id')
        group = Group.objects.get(id=group_id)
        context['group'] = group
        return context
