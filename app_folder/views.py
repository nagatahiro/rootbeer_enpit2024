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
import logging
logger = logging.getLogger(__name__)
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

class CameraView(LoginRequiredMixin, TemplateView):
    template_name = "app_folder/camera.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group_id = self.kwargs.get('group_id')
        group = get_object_or_404(CustomGroup, id=group_id)

        # Retrieve session data
        total_amount = self.request.session.pop('total_amount', None)
        store_name = self.request.session.pop('store_name', None)
        selected_member_id = self.request.session.pop('selected_member_id', None)

        # Find the selected member if ID exists
        selected_member = User.objects.filter(id=selected_member_id).first() if selected_member_id else None

        # Add data to the context
        context.update({
            'form': SplitBillForm(initial={
                'amount': total_amount,
                'members_count': group.members.count()
            }),
            'group': group,
            'members': group.members.all(),
            'result': self.request.session.pop('result', None),
            'store_name': store_name,
            'selected_member': selected_member,
            'total_amount': total_amount,
        })
        return context

    def post(self, request, *args, **kwargs):
        group_id = self.kwargs.get('group_id')
        group = get_object_or_404(CustomGroup, id=group_id)

        form = SplitBillForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            members_count = form.cleaned_data['members_count']
            selected_member_id = request.POST.get('selected_member')
            store_name = request.POST.get('store_name', '')

            # Validate members_count and calculate result
            if members_count > 0:
                result = amount / Decimal(members_count)
                
                # Store results in session
                request.session.update({
                    'result': float(result),
                    'total_amount': float(amount),
                    'store_name': store_name,
                    'selected_member_id': selected_member_id,
                })

                messages.success(request, f"1人あたりの金額: ¥{round(result, 2)}")
            else:
                messages.error(request, "人数を1以上にしてください。")
        else:
            messages.error(request, "無効な入力です。")

        return redirect('app_folder:camera', group_id=group_id)


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
    """グループ作成ページ"""
    template_name = "app_folder/create_group.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # セッションから検索結果と現在のグループ名を取得してコンテキストに渡す
        search_results = self.request.session.pop('search_results', [])
        current_group_name = self.request.session.get('current_group_name', '')
        selected_users = self.request.session.get('selected_users', [])
        context['search_results'] = search_results
        context['current_group_name'] = current_group_name
        context['selected_users'] = selected_users
        return context

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')

        if action == "search":
            # ユーザー検索処理
            search_query = request.POST.get('search_user', '').strip()
            group_name = request.POST.get('group_name', '').strip()

            # セッションから選択済みユーザーを取得
            selected_users = self.request.session.get('selected_users', [])

            # 新たに選択されたユーザーを追加
            new_selected_users = request.POST.getlist('invited_users')
            selected_users = list(set(selected_users + new_selected_users))  # 重複を排除
            self.request.session['selected_users'] = selected_users

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
                group = CustomGroup.objects.create(name=group_name, owner=request.user)

                group.members.add(request.user)

                if invited_users_ids:
                    invited_users = User.objects.filter(id__in=invited_users_ids)
                    group.members.add(*invited_users)
                    print(f"招待されたユーザー: {[user.username for user in invited_users]}")
                
                # セッションをクリア
                self.request.session.pop('selected_users', None)
                self.request.session.pop('current_group_name', None)

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
    
from decimal import Decimal
class GroupDetailView(LoginRequiredMixin, TemplateView):
    template_name = "app_folder/group_detail.html"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group_id = self.kwargs.get('group_id')
        group = get_object_or_404(CustomGroup, id=group_id)
        members_count = group.members.count()

        # セッションからデータを取得
        total_amount = self.request.session.pop('total_amount', None)
        store_name = self.request.session.pop('store_name', None)
        selected_member_id = self.request.session.pop('selected_member_id', None)

        # 選択されたメンバーの取得
        selected_member = None
        if selected_member_id:
            selected_member = User.objects.filter(id=selected_member_id).first()

        context['form'] = SplitBillForm(initial={
            'amount': total_amount,
            'members_count': members_count
            
        })
        context['group'] = group
        context['members'] = group.members.all()
        context['result'] = self.request.session.pop('result', None)
        context['store_name'] = store_name
        context['selected_member'] = selected_member
        context['total_amount'] = total_amount
        return context

    def post(self, request, *args, **kwargs):
        group_id = self.kwargs.get('group_id')
        group = get_object_or_404(CustomGroup, id=group_id)

        form = SplitBillForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            members_count = form.cleaned_data['members_count']
            selected_member_id = request.POST.get('selected_member')
            store_name = request.session.get('store_name')

            if members_count > 0:
                result = amount / Decimal(members_count)
                request.session['result'] = float(result)
                request.session['total_amount'] = float(amount)
                request.session['store_name'] = store_name
                request.session['selected_member_id'] = selected_member_id
                messages.success(request, f"1人あたりの金額: ¥{round(result, 2)}")
            else:
                messages.error(request, "人数を1以上にしてください。")
        else:
            messages.error(request, "無効な入力です。")

        return redirect('app_folder:group_detail', group_id=group_id)

from decimal import Decimal
class ShootingRegistration(LoginRequiredMixin, TemplateView):
    template_name = "app_folder/shooting_registration.html"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group_id = self.kwargs.get('group_id')
        group = get_object_or_404(CustomGroup, id=group_id)
        members_count = group.members.count()

        # セッションからデータを取得
        total_amount = self.request.session.pop('total_amount', None)
        store_name = self.request.session.pop('store_name', None)
        selected_member_id = self.request.session.pop('selected_member_id', None)

        # 選択されたメンバーの取得
        selected_member = None
        if selected_member_id:
            selected_member = User.objects.filter(id=selected_member_id).first()

        context['form'] = SplitBillForm(initial={
            'amount': total_amount,
            'members_count': members_count
            
        })
        context['group'] = group
        context['members'] = group.members.all()
        context['result'] = self.request.session.pop('result', None)
        context['store_name'] = store_name
        context['selected_member'] = selected_member
        context['total_amount'] = total_amount
        return context

    def post(self, request, *args, **kwargs):
        group_id = self.kwargs.get('group_id')
        group = get_object_or_404(CustomGroup, id=group_id)

        form = SplitBillForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            members_count = form.cleaned_data['members_count']
            selected_member_id = request.POST.get('selected_member')
            store_name = request.session.get('store_name')

            if members_count > 0:
                result = amount / Decimal(members_count)
                request.session['result'] = float(result)
                request.session['total_amount'] = float(amount)
                request.session['store_name'] = store_name
                request.session['selected_member_id'] = selected_member_id
                messages.success(request, f"1人あたりの金額: ¥{round(result, 2)}")
            else:
                messages.error(request, "人数を1以上にしてください。")
        else:
            messages.error(request, "無効な入力です。")

        return redirect('app_folder:shooting_registration', group_id=group_id)



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
            context['search_results'] = None

        context['search_query'] = search_query
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
        # 複数のパターンを試す
        patterns = [
            r'合計\s*[¥￥]\s*(\d+(?:,\d+)?)',  # 合計 ¥1,727
            r'食計\s*\d+点\s*[¥￥]\s*(\d+(?:,\d+)?)',  # 食計 3点 ¥1,727
            r'小計\s*[¥￥]\s*(\d+(?:,\d+)?)'   # 小計 ¥1,727
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                # カンマを除去してから数値に変換
                amount_str = match.group(1).replace(',', '')
                try:
                    # 金額が整数でない場合もfloatからintに変換
                    return int(float(amount_str))
                except ValueError:
                    continue
        
        return None


    def extract_store_name(self, text_annotations, checking_line_num=5):
        """
        テキストの縦幅順にソートして店名を抽出する
        特定の無関係なキーワードを回避
        """
        def calc_bbox_height(bounding_box):
            """バウンディングボックスの高さを計算する"""
            y_coords = [vertex.y for vertex in bounding_box.vertices]
            return max(y_coords) - min(y_coords)

        heights_and_texts = []
        excluded_keywords = [
            "領収", "クレジット", "決済", "TEL", "株式会社", 
            "No", "店No", "伝票", "登録番号", "時間", "日付"
        ]

        # 上からN行のデータを評価
        for annotation in text_annotations[:checking_line_num + 3]:  # 評価行数を増やす
            description = annotation.description.strip()
            
            # 空文字列や数字のみの行をスキップ
            if not description or description.isdigit():
                continue
            
            # 除外キーワードを含む行をスキップ
            if any(keyword in description for keyword in excluded_keywords):
                continue

            bounding_box = annotation.bounding_poly
            height = calc_bbox_height(bounding_box)
            
            # 一定以上の高さがある行のみを候補とする
            if height > 20:  # この閾値は調整が必要かもしれません
                heights_and_texts.append([height, description])

        # 縦幅順にソート（降順）
        sorted_texts = sorted(heights_and_texts, key=lambda x: x[0], reverse=True)

        # 最も適切な店名候補を返す
        if sorted_texts:
            # 最初の2つの候補から長い方を選択（より詳細な店名の可能性が高い）
            if len(sorted_texts) >= 2:
                first_candidate = sorted_texts[0][1]
                second_candidate = sorted_texts[1][1]
                return first_candidate if len(first_candidate) >= len(second_candidate) else second_candidate
            return sorted_texts[0][1]

        return None  # 適切な店名が見つからない場合はNoneを返す

    def post(self, request, *args, **kwargs):
        try:
            # リクエストから画像データを取得
            logger.info("リクエスト受信: %s", request.POST)
            image_data = request.POST.get('image')
            if not image_data:
                return JsonResponse({'status': 'error', 'message': '画像データがありません。'})

            # Base64データをデコード
            _, encoded = image_data.split(",", 1)
            image_bytes = base64.b64decode(encoded)

            # Google Cloud Vision API クライアントの初期化
            client = vision.ImageAnnotatorClient()
            image = vision.Image(content=image_bytes)

            # テキスト認識をリクエスト
            response = client.text_detection(image=image)
            texts = response.text_annotations
            if not texts:
                return JsonResponse({
                    'status': 'error',
                    'message': 'テキストが検出されませんでした。'
                })

            extracted_text = texts[0].description

            # 店名と合計金額を抽出
            store_name = self.extract_store_name(texts[1:])
            total_amount = self.extract_total_amount(extracted_text)
            
            # セッションに保存
            request.session['store_name'] = store_name if store_name else None
            if total_amount is not None:
                request.session['total_amount'] = total_amount

            # レスポンスデータの作成
            response_data = {
                'status': 'success',
                'store_name': store_name if store_name else None,
                'extracted_text': extracted_text,
                'total_amount': total_amount,
                'formatted_total': f'¥{total_amount}' if total_amount is not None else None
            }

            return JsonResponse(response_data)

        except Exception as e:
            logger.error(f"エラー: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)})

# EditGroupViewをedit_groupとしてエクスポート
edit_group = EditGroupView.as_view()