from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import TemplateView
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import login
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.views.generic.edit import CreateView
from django.db.models import Q
from django.db import connections, transaction
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib.auth.models import Group, User
from .models import CustomGroup, Purchase, PaymentDetail
from .forms import SignUpForm, SplitBillForm
from google.cloud import vision
from django.contrib.auth.decorators import login_required
from django.utils.crypto import get_random_string
from . import forms
from urllib.parse import urljoin
import logging
import numpy as np
import cv2
import base64
from pytesseract import image_to_string
import os
from decimal import Decimal, InvalidOperation
import re
from django.core.files.base import ContentFile
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Purchase, CustomGroup
import uuid


logger = logging.getLogger(__name__)


#ログアウト時にリダイレクトされるビュー
class TopView(TemplateView):
    template_name = "app_folder/top.html"

class HowToView(LoginRequiredMixin, TemplateView):
    template_name = "app_folder/howtouse.html"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    
#グループのホームページ、自身の収支が確認できる
class AccountingDetailsView(LoginRequiredMixin, TemplateView):
    template_name = 'app_folder/accounting_details.html'

    def get_context_data(self, **kwargs):
        # URLからpurchase_idを取得
        purchase_id = kwargs.get('purchase_id')
        # 該当のPurchaseオブジェクトを取得
        purchase = get_object_or_404(Purchase, id=purchase_id)
        # 関連するPaymentDetailを取得
        payment_details = purchase.payment_details.all()

        # コンテキストデータを返す
        context = {
            'purchase': purchase,
            'payment_details': payment_details,
        }
        return context
        

#ログイン時に使用
class LoginView(LoginView):
    """ログインページ"""
    form_class = forms.LoginForm
    template_name = "app_folder/login.html"

#ログアウト時に使用
class LogoutView(LoginRequiredMixin, LogoutView):
    """ログアウトページ"""
    template_name = "app_folder:top"

#アカウント作成の際に使用
class SignUp(CreateView):
    form_class = SignUpForm
    template_name = "app_folder/signup.html"
    success_url = reverse_lazy('app_folder:home')

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        self.object = user
        return HttpResponseRedirect(self.get_success_url())
    
#グループ一覧が表示されるページ
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

#グループ作成の際に使用する
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

        if action == "create":
            group_name = request.POST.get('group_name', '').strip()
            invited_users_ids = request.POST.getlist('invited_users')

            if group_name:
                group = CustomGroup.objects.create(name=group_name, owner=request.user)
                group.members.add(request.user)

                if invited_users_ids:
                    invited_users = User.objects.filter(id__in=invited_users_ids)
                    group.members.add(*invited_users)

                # 招待URLを生成
                invite_token = get_random_string(32)
                group.invite_token = invite_token
                group.save()

                #invite_url = request.build_absolute_uri(reverse('app_folder:join_group', args=[invite_token]))

                # グループ詳細ページにリダイレクト
                return redirect('app_folder:group_detail', group_id=group.id)

            else:
                messages.error(request, "グループ名を入力してください。")

            return redirect('app_folder:create_group')
        
@login_required
def join_group(request, token):
    group = get_object_or_404(CustomGroup, invite_token=token)
    
    # すでにグループのメンバーであればリダイレクト
    if request.user in group.members.all():
        return redirect('app_folder:group_detail', group_id=group.id)
    
    # メンバーに追加
    group.members.add(request.user)
    return redirect('app_folder:group_detail', group_id=group.id)

        
        
#グループを編集する際に使用
class EditGroupView(LoginRequiredMixin, TemplateView):
    """グループ編集ページ"""
    template_name = "app_folder/edit_group.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group_id = self.kwargs.get('group_id')
        group = CustomGroup.objects.get(id=group_id)
        context['group'] = group
        context['members'] = group.members.all()
        # 招待URLを生成
        base_url = 'https://{}'.format(self.request.get_host())
        invite_url = urljoin(
            base_url,
            reverse('app_folder:join_group', args=[group.invite_token])
        )
        context['invite_url'] = invite_url

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

#カメラ起動と文字抽出の際のビュー
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
from django.db.models import Sum



@login_required
def delete_purchase(request, purchase_id):
    purchase = get_object_or_404(Purchase, id=purchase_id)
    if purchase.user == request.user or request.user in purchase.group.members.all():
        purchase.delete()
    return HttpResponseRedirect(reverse('app_folder:group_detail', args=[purchase.group.id]))


#グループのホームページ、自身の収支が確認できる
class GroupDetailView(LoginRequiredMixin, TemplateView):
    template_name = "app_folder/group_detail.html"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group_id = self.kwargs.get('group_id')
        group = get_object_or_404(CustomGroup, id=group_id)

        # 招待URLを生成
        base_url = 'https://{}'.format(self.request.get_host())
        invite_url = urljoin(
            base_url,
            reverse('app_folder:join_group', args=[group.invite_token])
        )
        context['invite_url'] = invite_url

        # 合計金額計算
        purchases = Purchase.objects.filter(group=group).order_by('-date')
        total_amount = Decimal(purchases.aggregate(Sum('total_amount'))['total_amount__sum'] or 0)

        payment_info_list = [] 
        payment_user = []
        for i in purchases:
            if PaymentDetail.objects.filter(purchase=i).exists():
                details = PaymentDetail.objects.filter(purchase=i)
                total_amount -= i.total_amount
                payment_user.append({'user': i.user, 'total_amount': i.total_amount})

                for detail in details:
                    if i.user != detail.user:
                        payment_info_list.append({
                            'purchase': i,
                            'purchase_user': i.user,
                            'payment_user': detail.user,
                            'amount_paid': detail.amount_paid
                        })

        # ユーザーごとの損益計算
        members = group.members.all()
        user_totals = {
            user: Decimal(purchases.filter(user=user).aggregate(Sum('total_amount'))['total_amount__sum'] or 0)
            for user in members
        }

        for user, total in user_totals.items():
            for payment_us in payment_user:
                if payment_us['user'] == user:
                    total -= payment_us['total_amount']
            user_totals[user] = total

        num_members = Decimal(len(members))
        adjusted_totals = {}
        user_remainder = {}

        for user, total in user_totals.items():
            divisible_total = (total // num_members) * num_members
            adjusted_totals[user] = divisible_total
            user_remainder[user] = total - divisible_total
            total_amount -= user_remainder[user]

        # 損失計算
        user_losses = {}
        for user in members:
            paid_by_user = sum(
                item['amount_paid'] for item in payment_info_list if item['purchase_user'] == user
            )
            paid_to_user = sum(
                item['amount_paid'] for item in payment_info_list if item['payment_user'] == user
            )

            loss = (
                (adjusted_totals[user] / num_members) * (num_members - Decimal(1)) -
                ((total_amount - adjusted_totals[user]) / num_members) +
                (paid_by_user - paid_to_user)
            )

            user_losses[user.username] = int(round(loss, 2))

        # 支払い計算
        payments = {}
        for payer in members:
            for payee in members:
                if payer != payee:
                    payer_amount = adjusted_totals[payer] / num_members
                    payee_amount = adjusted_totals[payee] / num_members
                    for i in payment_info_list:
                        if i['purchase_user']==payer and i['payment_user']==payee:
                            payer_amount+=i['amount_paid']
                        elif i['purchase_user']==payee and i['payment_user']==payer:
                            payee_amount+=i['amount_paid']
                    amount_to_pay = round(payer_amount - payee_amount, 2)

                    if amount_to_pay > 0:
                        if payer.username not in payments:
                            payments[payer.username] = {}
                        payments[payer.username][payee.username] = int(amount_to_pay)

        context.update({
            'group': group,
            'members': members,
            'total_amount': total_amount,
            'user_losses': user_losses,
            'payments': payments,
            'purchases': purchases,
            'invite_url': invite_url,
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
            print("Form is valid:", form.is_valid()) 
            print(form.errors)  # エラー内容を表示
            logger.error(f"Form is invalid: {form.errors}")
            messages.error(request, "無効な入力です。")

        return redirect('app_folder:group_detail', group_id=group_id)


#購入時の登録の際に使用
from django.shortcuts import redirect
from django.contrib import messages
import logging
import re
from decimal import Decimal
from django.db import transaction

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
            image_data = request.POST.get('image')
            group_id = request.POST.get('group_id')

            if not image_data or not group_id:
                return JsonResponse({'status': 'error', 'message': '画像またはグループIDがありません。'})

            # Base64データをセッションに保存
            request.session['receipt_image'] = image_data

            # Google Cloud Vision APIでテキスト検出
            client = vision.ImageAnnotatorClient()
            _, encoded = image_data.split(",", 1)
            image_bytes = base64.b64decode(encoded)
            image = vision.Image(content=image_bytes)
            response = client.text_detection(image=image)
            texts = response.text_annotations

            if not texts:
                return JsonResponse({'status': 'error', 'message': 'テキストが検出されませんでした。'})

            extracted_text = texts[0].description
            store_name = self.extract_store_name(texts[1:])
            total_amount = self.extract_total_amount(extracted_text)

            # セッションに解析結果を保存
            request.session['store_name'] = store_name or "未設定"
            request.session['total_amount'] = total_amount or 0

            return JsonResponse({
                'status': 'success',
                'store_name': store_name,
                'total_amount': total_amount,
                'formatted_total': f'¥{total_amount}' if total_amount else None
            })

        except Exception as e:
            logger.error(f"PhotographViewエラー: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)})

# 登録処理
class ShootingRegistration(LoginRequiredMixin, TemplateView):
    template_name = "app_folder/shooting_registration.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group_id = self.kwargs.get('group_id')
        group = get_object_or_404(CustomGroup, id=group_id)

        context.update({
            'group': group,
            'members': group.members.all(),
            'store_name': self.request.session.get('store_name', ''),
            'total_amount': self.request.session.get('total_amount', ''),
        })
        return context

    def post(self, request, *args, **kwargs):
        group_id = self.kwargs.get('group_id')
        group = get_object_or_404(CustomGroup, id=group_id)

        form_data = request.POST
        selected_member_id = form_data.get('selected_member')
        store_name = form_data.get('store_name')
        total_amount = form_data.get('total_amount')

        try:
            # 画像データを取得
            receipt_image_data = request.session.get('receipt_image')
            image_file = None
            if receipt_image_data:
                _, encoded = receipt_image_data.split(",", 1)
                image_bytes = base64.b64decode(encoded)
                file_name = f"receipt_{uuid.uuid4().hex}.jpg"
                image_file = ContentFile(image_bytes, name=file_name)

            # Purchase作成
            selected_member = User.objects.get(id=selected_member_id)
            total_amount_clean = re.sub(r'[^\d.]', '', str(total_amount))  # 金額の整形
            try:
                total_amount_decimal = Decimal(total_amount_clean)
            except InvalidOperation:
                messages.error(request, "合計金額の形式が無効です。")
                return redirect('app_folder:group_detail', group_id=group_id)

            payment_details = []
            total_payment_details = Decimal('0')

            # 支払い詳細の取得
            for member in group.members.all():
                key = f'payment_details_{member.id}'
                if key in form_data and form_data[key].strip():
                    amount_str = form_data[key].strip()
                    amount_clean = re.sub(r'[^\d.]', '', amount_str)

                    try:
                        amount = Decimal(amount_clean)
                        payment_details.append({
                            'user': member,
                            'amount_paid': amount
                        })
                        total_payment_details += amount
                    except InvalidOperation:
                        messages.error(request, f"{member.username} の支払額の形式が無効です。")
                        return redirect('app_folder:group_detail', group_id=group_id)

            with transaction.atomic():
                # Purchaseインスタンスを作成
                purchase = Purchase.objects.create(
                    group=group,
                    user=selected_member,
                    total_amount=total_amount_decimal,
                    store_name=store_name,
                    receipt_image=image_file
                )

                # 詳細設定の全てが未入力の場合
                if not payment_details:
                    request.session['purchase_id'] = purchase.id
                    request.session['total_amount'] = None
                    request.session['store_name'] = None
                    request.session['selected_member_id'] = None
                    messages.success(request, "購入情報が保存されました（詳細設定なし）。")
                    return redirect('app_folder:group_detail', group_id=group_id)

                # 合計金額チェック
                if total_payment_details > total_amount_decimal:
                    messages.error(request, "詳細設定の合計が合計金額を上回っています。")
                    return redirect('app_folder:group_detail', group_id=group_id)

                # 未入力のメンバーに分割金額を計算
                remaining_amount = total_amount_decimal - total_payment_details
                unset_members = [
                    member for member in group.members.all() 
                    if not any(detail['user'] == member for detail in payment_details)
                ]
                if unset_members:
                    split_amount = remaining_amount // len(unset_members)
                    remainder = remaining_amount % len(unset_members)

                    for i, member in enumerate(unset_members):
                        amount_paid = split_amount
                        if i == 0:  # 最初のメンバーが余りを負担
                            amount_paid += remainder
                        payment_details.append({
                            'user': member,
                            'amount_paid': amount_paid
                        })

                # PaymentDetailインスタンスを作成
                for detail in payment_details:
                    PaymentDetail.objects.create(
                        purchase=purchase,
                        user=detail['user'],
                        amount_paid=detail['amount_paid']
                    )

                # セッションのクリア
                request.session['purchase_id'] = purchase.id
                request.session['total_amount'] = None
                request.session['store_name'] = None
                request.session['selected_member_id'] = None

                # 成功メッセージ
                messages.success(request, "購入情報が保存されました。")

        except Exception as e:
            messages.error(request, f"購入情報の保存に失敗しました。詳細: {str(e)}")
            logger.error(f"Error saving purchase: {e}")

        return redirect('app_folder:group_detail', group_id=group_id)







# EditGroupViewをedit_groupとしてエクスポート
edit_group = EditGroupView.as_view()