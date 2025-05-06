from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Avg, Count
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Product, Category, Cart, CartItem, Wishlist, Review, ProductTracking
from .forms import ReviewForm
from apps.ai_assistant.utils import generate_ai_product_description
import time
import json

def home(request):
    featured_products = Product.objects.filter(status='active').order_by('-created_at')[:8]
    top_categories = Category.objects.annotate(product_count=Count('products')).order_by('-product_count')[:6]
    best_selling = Product.objects.filter(status='active').annotate(order_count=Count('order_items')).order_by('-order_count')[:8]
    top_rated = Product.objects.filter(status='active', reviews__isnull=False).annotate(avg_rating=Avg('reviews__rating')).order_by('-avg_rating')[:8]
    
    context = {
        'featured_products': featured_products,
        'top_categories': top_categories,
        'best_selling': best_selling,
        'top_rated': top_rated,
    }
    return render(request, 'products/home.html', context)

def product_list(request):
    categories = Category.objects.all()
    products = Product.objects.filter(status='active')
    
    # Фильтрация по категории
    category_slug = request.GET.get('category')
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)
    
    # Фильтрация по цене
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)
    
    # Поиск по названию или описанию
    search_query = request.GET.get('q')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) | 
            Q(description__icontains=search_query)
        )
    
    # Сортировка
    sort_by = request.GET.get('sort_by', 'newest')
    if sort_by == 'newest':
        products = products.order_by('-created_at')
    elif sort_by == 'price_low':
        products = products.order_by('price')
    elif sort_by == 'price_high':
        products = products.order_by('-price')
    elif sort_by == 'rating':
        products = products.annotate(avg_rating=Avg('reviews__rating')).order_by('-avg_rating')
    elif sort_by == 'popularity':
        products = products.annotate(order_count=Count('order_items')).order_by('-order_count')
    
    context = {
        'categories': categories,
        'products': products,
        'search_query': search_query,
        'sort_by': sort_by,
    }
    return render(request, 'products/product_list.html', context)

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, status='active')
    reviews = product.reviews.all().order_by('-created_at')
    related_products = Product.objects.filter(category=product.category).exclude(id=product.id)[:4]
    
    # Запись времени активности пользователя
    if request.user.is_authenticated:
        view_time_start = request.session.get(f'view_time_start_{product.id}')
        if not view_time_start:
            request.session[f'view_time_start_{product.id}'] = time.time()
        
        # Обновление счетчика просмотров и активности
        user_activity, created = request.user.activities.get_or_create(product=product)
        if not created:
            user_activity.view_count += 1
            user_activity.save()
    
    # Форма отзыва
    form = ReviewForm()
    can_review = False
    has_reviewed = False
    
    if request.user.is_authenticated:
        # Проверка, купил ли пользователь товар
        has_purchased = request.user.orders.filter(
            items__product=product, status='completed'
        ).exists()
        can_review = has_purchased
        has_reviewed = Review.objects.filter(product=product, user=request.user).exists()
    
    context = {
        'product': product,
        'reviews': reviews,
        'related_products': related_products,
        'form': form,
        'can_review': can_review,
        'has_reviewed': has_reviewed,
    }
    return render(request, 'products/product_detail.html', context)

@login_required
def leave_view_time(request, product_id):
    view_time_start = request.session.get(f'view_time_start_{product_id}')
    if view_time_start:
        view_time = int(time.time() - view_time_start)
        user_activity, created = request.user.activities.get_or_create(product_id=product_id)
        user_activity.view_time += view_time
        user_activity.save()
        del request.session[f'view_time_start_{product_id}']
    return JsonResponse({'status': 'success'})

@login_required
@require_POST
def add_to_cart(request):
    product_id = request.POST.get('product_id')
    quantity = int(request.POST.get('quantity', 1))
    
    product = get_object_or_404(Product, id=product_id, status='active')
    
    # Проверка доступности товара
    if product.stock < quantity:
        messages.error(request, f'Недостаточно товара в наличии. Доступно: {product.stock}')
        return redirect('product_detail', slug=product.slug)
    
    # Получение или создание корзины
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    # Добавление в корзину
    cart_item, item_created = CartItem.objects.get_or_create(cart=cart, product=product)
    
    if not item_created:
        cart_item.quantity += quantity
    else:
        cart_item.quantity = quantity
    
    cart_item.save()
    
    messages.success(request, 'Товар добавлен в корзину')
    return redirect('cart')

@login_required
def cart(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    context = {'cart': cart}
    return render(request, 'products/cart.html', context)

@login_required
@require_POST
def update_cart(request):
    data = json.loads(request.body)
    item_id = data.get('item_id')
    quantity = int(data.get('quantity'))
    
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    
    # Проверка доступности товара
    if cart_item.product.stock < quantity:
        return JsonResponse({
            'status': 'error',
            'message': f'Недостаточно товара в наличии. Доступно: {cart_item.product.stock}'
        })
    
    if quantity > 0:
        cart_item.quantity = quantity
        cart_item.save()
    else:
        cart_item.delete()
    
    cart = Cart.objects.get(user=request.user)
    
    return JsonResponse({
        'status': 'success',
        'subtotal': str(cart_item.subtotal) if quantity > 0 else "0",
        'total': str(cart.total_price),
        'item_count': cart.item_count
    })

@login_required
@require_POST
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart_item.delete()
    
    messages.success(request, 'Товар удалён из корзины')
    return redirect('cart')

@login_required
@require_POST
def add_to_wishlist(request):
    product_id = request.POST.get('product_id')
    product = get_object_or_404(Product, id=product_id, status='active')
    
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    
    if product in wishlist.products.all():
        wishlist.products.remove(product)
        added = False
        message = 'Товар удалён из списка желаний'
    else:
        wishlist.products.add(product)
        added = True
        message = 'Товар добавлен в список желаний'
    
    if request.is_ajax():
        return JsonResponse({
            'status': 'success',
            'added': added,
            'message': message
        })
    
    messages.success(request, message)
    return redirect('product_detail', slug=product.slug)

@login_required
def wishlist(request):
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    context = {'wishlist': wishlist}
    return render(request, 'products/wishlist.html', context)

@login_required
@require_POST
def submit_review(request, product_id):
    product = get_object_or_404(Product, id=product_id, status='active')
    
    # Проверка, купил ли пользователь товар
    has_purchased = request.user.orders.filter(
        items__product=product, status='completed'
    ).exists()
    
    if not has_purchased:
        messages.error(request, 'Вы можете оставить отзыв только после покупки товара')
        return redirect('product_detail', slug=product.slug)
    
    # Проверка, оставил ли пользователь уже отзыв
    has_reviewed = Review.objects.filter(product=product, user=request.user).exists()
    if has_reviewed:
        messages.error(request, 'Вы уже оставили отзыв на этот товар')
        return redirect('product_detail', slug=product.slug)
    
    form = ReviewForm(request.POST)
    if form.is_valid():
        review = form.save(commit=False)
        review.user = request.user
        review.product = product
        review.save()
        
        # Сохранение изображений отзыва
        for image in request.FILES.getlist('images'):
            ReviewImage.objects.create(review=review, image=image)
        
        messages.success(request, 'Ваш отзыв добавлен')
    else:
        messages.error(request, 'Пожалуйста, исправьте ошибки в форме')
    
    return redirect('product_detail', slug=product.slug)

@login_required
@require_POST
def track_product(request, product_id):
    product = get_object_or_404(Product, id=product_id, status='active')
    
    data = request.POST
    track_price = 'track_price' in data
    track_stock = 'track_stock' in data
    track_discount = 'track_discount' in data
    
    tracking, created = ProductTracking.objects.get_or_create(
        user=request.user,
        product=product,
        defaults={
            'track_price': track_price,
            'track_stock': track_stock,
            'track_discount': track_discount
        }
    )
    
    if not created:
        tracking.track_price = track_price
        tracking.track_stock = track_stock
        tracking.track_discount = track_discount
        tracking.save()
    
    messages.success(request, 'Настройки отслеживания товара обновлены')
    return redirect('product_detail', slug=product.slug)

class SellerDashboardMixin:
    """Миксин для проверки роли продавца"""
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_seller():
            messages.error(request, 'У вас нет доступа к панели продавца')
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)

@login_required
def seller_generate_description(request):
    if not request.user.is_seller():
        return JsonResponse({'status': 'error', 'message': 'У вас нет доступа к этой функции'})
    
    data = json.loads(request.body)
    product_name = data.get('name', '')
    product_attrs = data.get('attributes', {})
    
    try:
        description = generate_ai_product_description(product_name, product_attrs)
        return JsonResponse({'status': 'success', 'description': description})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})