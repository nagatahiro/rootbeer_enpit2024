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
from django.contrib.auth.models import User

from . import forms

class TopView(TemplateView):  # TopView の定義
    template_name = "app_folder/top.html"

class HomeView(LoginRequiredMixin, TemplateView):
    template_name = "app_folder/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['groups'] = Group.objects.all()  # すべてのグループを取得
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # セッションから検索結果を取得してコンテキストに渡す
        search_results = self.request.session.pop('search_results', [])
        context['search_results'] = search_results
        return context

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')

        if action == "search":
            # ユーザー検索処理
            search_query = request.POST.get('search_user', '')
            if search_query:
                search_results = list(User.objects.filter(username__icontains=search_query).values('id', 'username'))
                request.session['search_results'] = search_results
            else:
                request.session['search_results'] = []
            return redirect('app_folder:create_group')

        elif action == "create":
            # グループ作成処理
            group_name = request.POST.get('group_name')
            invited_users_ids = request.POST.getlist('invited_users')  # 招待するユーザーIDリスト

            if group_name:
                group, created = Group.objects.get_or_create(name=group_name)
                if invited_users_ids:
                    invited_users = User.objects.filter(id__in=invited_users_ids)
                    # ユーザーをグループに追加する処理
                    print(f"招待されたユーザー: {[user.username for user in invited_users]}")
                messages.success(request, f"グループ '{group_name}' を作成しました。")
            return redirect('app_folder:home')
        
        

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
