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
from .models import CustomGroup

from . import forms

class TopView(TemplateView):  # TopView の定義
    template_name = "app_folder/top.html"

class HomeView(LoginRequiredMixin, TemplateView):
    template_name = "app_folder/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 現在のユーザーが所有または所属しているグループを取得
        owned_groups = CustomGroup.objects.filter(owner=self.request.user)
        member_groups = CustomGroup.objects.filter(members=self.request.user)
        all_groups = owned_groups | member_groups  # これらを結合して渡す

        # 各グループごとにメンバーを取得
        groups_with_members = []
        for group in all_groups.distinct():  # 重複を削除
            groups_with_members.append({
                'group': group,
                'members': group.members.all()  # グループのメンバーリスト
            })

        context['groups_with_members'] = groups_with_members
        return context


class LoginView(LoginView):
    """ログインページ"""
    form_class = forms.LoginForm
    template_name = "app_folder/login.html"

class LogoutView(LoginRequiredMixin, LogoutView):
    """ログアウトページ"""
    template_name = "app_folder:top"

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
        # セッションから検索結果と現在のグループ名を取得してコンテキストに渡す
        search_results = self.request.session.pop('search_results', [])
        current_group_name = self.request.session.pop('current_group_name', '')
        context['search_results'] = search_results
        context['current_group_name'] = current_group_name
        return context

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')

        if action == "search":
            # ユーザー検索処理
            search_query = request.POST.get('search_user', '').strip()
            group_name = request.POST.get('group_name', '').strip()

            # グループ名をセッションに保存
            request.session['current_group_name'] = group_name

            if search_query:
                # 検索結果を取得（自分以外のユーザーのみ表示）
                search_results = list(
                    User.objects.filter(username__icontains=search_query)
                    .exclude(id=request.user.id)  # 自分自身を検索結果から除外
                    .values('id', 'username')
                )
                request.session['search_results'] = search_results
            else:
                request.session['search_results'] = []

            return redirect('app_folder:create_group')

        elif action == "create":
            # グループ作成処理
            group_name = request.POST.get('group_name', '').strip()
            invited_users_ids = request.POST.getlist('invited_users')  # 招待するユーザーIDリスト

            if group_name:
                # グループを作成
                group, created = CustomGroup.objects.get_or_create(name=group_name, owner=request.user)

                if invited_users_ids:
                    invited_users = User.objects.filter(id__in=invited_users_ids)
                    group.members.add(*invited_users)
                    print(f"招待されたユーザー: {[user.username for user in invited_users]}")

                messages.success(request, f"グループ '{group_name}' を作成しました。")
            else:
                messages.error(request, "グループ名を入力してください。")

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
        group = CustomGroup.objects.get(id=group_id)
        context['group'] = group
        context['members'] = group.members.all()  # グループメンバー
        return context


class EditGroupView(LoginRequiredMixin, TemplateView):
    """グループ編集ページ"""
    template_name = "app_folder/edit_group.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group_id = self.kwargs.get('group_id')
        group = CustomGroup.objects.get(id=group_id)
        context['group'] = group
        context['members'] = group.members.all()
        context['all_users'] = User.objects.exclude(id__in=group.members.all())  # まだメンバーになっていないユーザー
        return context

    def post(self, request, *args, **kwargs):
        group_id = self.kwargs.get('group_id')
        group = CustomGroup.objects.get(id=group_id)

        # 新しいメンバーを追加
        new_members_ids = request.POST.getlist('new_members')
        if new_members_ids:
            new_members = User.objects.filter(id__in=new_members_ids)
            group.members.add(*new_members)

        # メンバーを削除
        remove_members_ids = request.POST.getlist('remove_members')
        if remove_members_ids:
            remove_members = User.objects.filter(id__in=remove_members_ids)
            group.members.remove(*remove_members)

        return redirect('app_folder:group_detail', group_id=group_id)

