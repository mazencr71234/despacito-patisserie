from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.hashers import check_password, make_password
from .models import Category, MenuItem, Order, OrderItem, SiteSetting
import json

# ========== القائمة الرئيسية ==========
def menu(request):
    categories = Category.objects.prefetch_related('items').all()
    return render(request, 'orders/menu.html', {'categories': categories})

# ========== إضافة عنصر للسلة (POST) ==========
def add_to_cart(request, item_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)

    item = get_object_or_404(MenuItem, id=item_id, available=True)
    cart = request.session.get('cart', {})
    cart[str(item_id)] = cart.get(str(item_id), 0) + 1
    request.session['cart'] = cart
    request.session.modified = True
    return JsonResponse({'success': True, 'cart_count': sum(cart.values())})

# ========== API لجلب محتويات السلة ==========
def get_cart_json(request):
    cart = request.session.get('cart', {})
    items_data = []
    total = 0
    for item_id, qty in cart.items():
        try:
            item = MenuItem.objects.get(id=int(item_id), available=True)
            subtotal = float(item.price) * qty
            items_data.append({
                'id': item.id,
                'name': item.name,
                'price': float(item.price),
                'quantity': qty,
                'subtotal': subtotal,
                'image_url': item.image.url if item.image else None,
            })
            total += subtotal
        except MenuItem.DoesNotExist:
            pass
    return JsonResponse({'items': items_data, 'total': total, 'cart_count': sum(cart.values())})

# ========== API للمفضلة ==========
def get_wishlist_json(request):
    if request.method != 'POST':
        return JsonResponse({'items': []})
    try:
        data = json.loads(request.body)
        wishlist_ids = data.get('ids', [])
    except:
        return JsonResponse({'items': []})

    items_data = []
    for item_id in wishlist_ids:
        try:
            item = MenuItem.objects.get(id=int(item_id), available=True)
            items_data.append({
                'id': item.id,
                'name': item.name,
                'price': float(item.price),
                'image_url': item.image.url if item.image else None,
            })
        except MenuItem.DoesNotExist:
            pass
    return JsonResponse({'items': items_data})

# ========== تعديل كمية عنصر في السلة ==========
def update_cart(request, item_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)

    try:
        data = json.loads(request.body)
        new_qty = int(data.get('quantity', 1))
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)

    cart = request.session.get('cart', {})
    if new_qty > 0:
        cart[str(item_id)] = new_qty
    else:
        cart.pop(str(item_id), None)

    request.session['cart'] = cart
    request.session.modified = True
    return JsonResponse({'success': True})

# ========== حذف عنصر من السلة ==========
def remove_from_cart(request, item_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)

    cart = request.session.get('cart', {})
    cart.pop(str(item_id), None)
    request.session['cart'] = cart
    request.session.modified = True
    return JsonResponse({'success': True})

# ========== صفحة عرض السلة (منفصلة) ==========
def cart_view(request):
    cart = request.session.get('cart', {})
    items = []
    total = 0
    for item_id, qty in cart.items():
        try:
            item = MenuItem.objects.get(id=int(item_id), available=True)
            subtotal = item.price * qty
            items.append({'item': item, 'quantity': qty, 'subtotal': subtotal})
            total += subtotal
        except MenuItem.DoesNotExist:
            pass
    return render(request, 'orders/cart.html', {'items': items, 'total': total})

# ========== إتمام الطلب ==========
def checkout(request):
    cart = request.session.get('cart', {})
    if not cart:
        messages.error(request, "السلة فارغة")
        return redirect('menu')

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        table = request.POST.get('table', '').strip()
        phone = request.POST.get('phone', '').strip()
        confirm_input = request.POST.get('confirmation_input', '').strip()

        if not all([name, table, phone, confirm_input]):
            messages.error(request, "جميع الحقول مطلوبة (الاسم، رقم الطاولة، الهاتف، رقم التأكيد)")
            return redirect('checkout')

        # جلب رقم التأكيد الصحيح من الإعدادات
        site_setting = SiteSetting.objects.first()
        correct_code = site_setting.confirmation_code if site_setting else 'mazen123'

        if not check_password(confirm_input, correct_code):
            messages.error(request, "رقم التأكيد غير صحيح")
            return redirect('checkout')

        # حساب الإجمالي وإعداد عناصر الطلب
        total = 0
        order_items = []
        for item_id, qty in cart.items():
            try:
                item = MenuItem.objects.get(id=int(item_id), available=True)
                subtotal = item.price * qty
                total += subtotal
                order_items.append(OrderItem(menu_item=item, quantity=qty, item_price=item.price))
            except MenuItem.DoesNotExist:
                pass

        if not order_items:
            messages.error(request, "المنتجات المطلوبة غير متاحة حالياً")
            return redirect('menu')

        order = Order.objects.create(
            customer_name=name,
            table_number=table,
            phone=phone,
            total_price=total,
            status='pending'
        )
        for oi in order_items:
            oi.order = order
        OrderItem.objects.bulk_create(order_items)

        # إفراغ السلة
        request.session['cart'] = {}
        request.session.modified = True
        messages.success(request, "تم إرسال طلبك بنجاح!")
        return redirect('order_confirmation', order_id=order.id)

    # GET request
    return render(request, 'orders/checkout.html')

# ========== صفحة تأكيد الطلب ==========
def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'orders/confirmation.html', {'order': order})

# ========== لوحة تحكم الأدمن (تتطلب staff) ==========
@staff_member_required
def admin_dashboard(request):
    site_setting = SiteSetting.objects.first()

    if request.method == 'POST':
        # تغيير رقم التأكيد العام
        if 'update_code' in request.POST:
            new_code = request.POST.get('new_confirmation_code', '').strip()
            if new_code:
                if site_setting:
                    site_setting.confirmation_code = new_code
                    site_setting.save()
                else:
                    SiteSetting.objects.create(confirmation_code=new_code)
                messages.success(request, "تم تحديث رقم التأكيد")
            return redirect('admin_dashboard')
        else:
            # تغيير حالة طلب أو رقم تأكيد الطلب نفسه
            order_id = request.POST.get('order_id')
            new_status = request.POST.get('status')
            new_code = request.POST.get('confirmation_code', '').strip()
            try:
                order = Order.objects.get(id=order_id)
                if new_status in dict(Order.STATUS_CHOICES):
                    order.status = new_status
                order.confirmation_code = new_code if new_code else None
                order.save()
            except Order.DoesNotExist:
                pass
            return redirect('admin_dashboard')

    orders = Order.objects.all().order_by('-created_at')
    today = timezone.now().date()
    first_of_month = today.replace(day=1)

    daily_profit = Order.objects.filter(
        created_at__date=today, status__in=['confirmed', 'delivered']
    ).aggregate(total=Sum('total_price'))['total'] or 0

    monthly_profit = Order.objects.filter(
        created_at__date__gte=first_of_month, status__in=['confirmed', 'delivered']
    ).aggregate(total=Sum('total_price'))['total'] or 0

    return render(request, 'orders/dashboard.html', {
        'orders': orders,
        'daily_profit': daily_profit,
        'monthly_profit': monthly_profit,
        'site_setting': site_setting,
    })