from django.shortcuts import render, redirect
from django.views import View
from django.views.generic import TemplateView  
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse_lazy, reverse
from django.views.generic.edit import CreateView
from django.contrib.auth import login
from django.urls import reverse
from .forms import SignUpForm
from django.contrib import messages
from django.contrib.auth.models import Group
from django.contrib.auth.models import User
from .models import CustomGroup
from django.shortcuts import render, get_object_or_404
from .models import CustomGroup
from .forms import SplitBillForm
from django.db.models import Q

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
    template_name = "app_folder/create_group.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_results'] = self.request.session.pop('search_results', [])
        context['current_group_name'] = self.request.session.get('current_group_name', '')
        context['selected_users'] = self.request.session.get('selected_users', [])
        return context

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')

        if action == "search":
            search_query = request.POST.get('search_user', '').strip()
            group_name = request.POST.get('group_name', '').strip()
            selected_users = self.request.session.get('selected_users', [])

            new_selected_users = request.POST.getlist('invited_users')
            selected_users = list(set(selected_users + new_selected_users))
            self.request.session['selected_users'] = selected_users
            self.request.session['current_group_name'] = group_name

            if search_query:
                search_results = list(
                    User.objects.filter(username__icontains=search_query)
                    .exclude(id=request.user.id)
                    .values('id', 'username')
                )
                request.session['search_results'] = search_results
            else:
                request.session['search_results'] = []

            return redirect('app_folder:create_group')

        elif action == "create":
            group_name = request.POST.get('group_name', '').strip()
            invited_users_ids = self.request.session.get('selected_users', [])

            if group_name and invited_users_ids:
                group = CustomGroup.objects.create(name=group_name, owner=request.user)
                group.members.add(request.user)
                invited_users = User.objects.filter(id__in=invited_users_ids)
                group.members.add(*invited_users)

                messages.success(request, f"グループ '{group_name}' を作成しました。")
                self.request.session.pop('selected_users', None)
                self.request.session.pop('current_group_name', None)
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
    
# from decimal import Decimal
# class GroupDetailView(LoginRequiredMixin, TemplateView):
#     template_name = "app_folder/group_detail.html"
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         group_id = self.kwargs.get('group_id')
#         group = get_object_or_404(CustomGroup, id=group_id)
#         members_count = group.members.count()  # メンバー数を取得

#         # セッションから合計金額を取得
#         total_amount = self.request.session.pop('total_amount', None)

#         # フォームの初期値として合計金額を設定
#         context['form'] = SplitBillForm(initial={
#             'amount': total_amount,
#             'members_count': members_count
#         })
#         context['group'] = group
#         context['members'] = group.members.all()
#         context['result'] = self.request.session.pop('result', None)  # 計算結果をセッションから取得
#         return context

from django.views.generic import TemplateView
from django.shortcuts import get_object_or_404

class GroupDetailView(LoginRequiredMixin, TemplateView):
    template_name = "app_folder/group_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group_id = self.kwargs.get('group_id')
        group = get_object_or_404(CustomGroup, id=group_id)
        members = group.members.all()  # グループのメンバー
        purchases = group.purchases.all()  # グループに関連付けられた購入データ

        context['group'] = group
        context['purchases'] = purchases
        context['members'] = members  # メンバーリストを追加
        context['members_count'] = members.count()  # メンバー数を追加
        return context


    def post(self, request, *args, **kwargs):
        group_id = self.kwargs.get('group_id')
        group = get_object_or_404(CustomGroup, id=group_id)

        form = SplitBillForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            members_count = form.cleaned_data['members_count']
            if members_count > 0:
                result = amount / Decimal(members_count)  # Decimalを使用
                request.session['result'] = float(result)  # floatに変換して保存
                messages.success(request, f"1人あたりの金額: ¥{round(result, 2)}")
            else:
                messages.error(request, "人数を1以上にしてください。")
        else:
            messages.error(request, "無効な入力です。")

        return redirect('app_folder:group_detail', group_id=group_id)




class EditGroupView(LoginRequiredMixin, TemplateView):
    """グループ編集ページ"""
    template_name = "app_folder/edit_group.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group_id = self.kwargs.get('group_id')
        group = CustomGroup.objects.get(id=group_id)
        context['group'] = group
        context['members'] = group.members.all()

        # 検索クエリがあればそれに基づいて結果を返す
        search_query = self.request.GET.get('search', '')

        if search_query:
            # 検索結果を取得（部分一致検索 + 現在のメンバー以外のユーザー）
            context['search_results'] = User.objects.filter(
                Q(username__icontains=search_query) | Q(email__icontains=search_query)
            ).exclude(id__in=group.members.all())
        else:
            context['search_results'] = []
        
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
        
        # グループ消去処理
        if 'delete_group' in request.POST:
            if request.user == group.owner:  # 所有者のみ消去可能
                group.delete()
                messages.success(request, "グループが消去されました。")
                return redirect('app_folder:home')
            else:
                messages.error(request, "グループの消去権限がありません。")

        return redirect('app_folder:group_detail', group_id=group_id)

    def get_success_url(self):
        # 成功後にリダイレクトする URL を指定
        return reverse('app_folder:home')

class PhotographView(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'app_folder/photograph.html')

    def extract_total_amount(self, text):
        """レシートテキストから合計金額を抽出する"""
        import re
        pattern = r'合計\s¥(\d+(,\d+))'
        match = re.search(pattern, text)
        if match:
            total_amount = match.group(1).replace(',', '')
            return int(total_amount)  # 数値として返す
        return None

    def post(self, request, *args, **kwargs):
        try:
            # リクエストから画像データを取得
            image_data = request.POST.get('image')
            if not image_data:
                return JsonResponse({'status': 'error', 'message': '画像データがありません。'})

            # Base64データをデコード
            _, encoded = image_data.split(",", 1)
            image_bytes = base64.b64decode(encoded)

            # Google Cloud Vision API クライアントの初期化
            client = vision.ImageAnnotatorClient()

            # Vision API 用の画像オブジェクト作成
            image = vision.Image(content=image_bytes)

            # テキスト認識をリクエスト
            response = client.text_detection(image=image)

            # 抽出されたテキスト
            texts = response.text_annotations
            if not texts:
                return JsonResponse({
                    'status': 'error',
                    'message': 'テキストが検出されませんでした。'
                })

            extracted_text = texts[0].description
            
            # 合計金額を抽出
            total_amount = self.extract_total_amount(extracted_text)
            
            if total_amount is not None:
            # 合計金額をセッションに保存
                request.session['total_amount'] = total_amount

            # レスポンスデータの作成
            response_data = {
                'status': 'success',
                'extracted_text': extracted_text,
                'total_amount': total_amount,
                'formatted_total': f'¥{total_amount}' if total_amount is not None else None
            }
            
            # ここで必要に応じてデータベースに保存などの処理を追加できます
            # 例：
            # Receipt.objects.create(
            #     total_amount=total_amount,
            #     raw_text=extracted_text,
            #     # その他必要なフィールド
            # )

            return JsonResponse(response_data)

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

# EditGroupViewをedit_groupとしてエクスポート
edit_group = EditGroupView.as_view()


#追加↓
from django.views.generic.edit import CreateView
from django.urls import reverse_lazy
from .models import Purchase
from .forms import PurchaseForm
from django.contrib.auth.mixins import LoginRequiredMixin

class AddPurchaseView(LoginRequiredMixin, CreateView):
    model = Purchase
    form_class = PurchaseForm
    template_name = "app_folder/add_purchase.html"
    success_url = reverse_lazy('app_folder:home')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user  # 現在のユーザーをフォームに渡す
        return kwargs

    def form_valid(self, form):
        form.instance.purchaser = self.request.user  # 購入者をログイン中のユーザーに設定
        return super().form_valid(form)