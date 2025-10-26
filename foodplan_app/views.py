from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import MenuType, FoodTag, UserPage, Subscription, User, Recipe
from .forms import EmailAuthenticationForm, CustomUserCreationForm

from django.utils import timezone

try:
    from .models import PromoCode  # если модели нет — всё продолжит работать без скидки
except Exception:
    PromoCode = None
from django.db.models.fields.related import ForeignKey


def index(request):
    return render(request, 'index.html')


def auth_view(request):
    if request.user.is_authenticated:
        return redirect('lk')

    if request.method == 'POST':
        form = EmailAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Добро пожаловать, {user.username}!')

            next_url = request.POST.get('next') or request.GET.get('next') or 'lk'
            return redirect(next_url)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{error}')
    else:
        form = EmailAuthenticationForm()

    next_url = request.GET.get('next', '')

    return render(request, 'registration/auth.html', {
        'form': form,
        'next': next_url
    })


def registration_view(request):
    if request.user.is_authenticated:
        return redirect('lk')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserPage.objects.create(user=user, username=user.username)
            login(request, user)
            messages.success(request, f'Аккаунт создан для {user.username}!')
            return redirect('lk')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{error}')
    else:
        form = CustomUserCreationForm()

    return render(request, 'registration/registration.html', {'form': form})


@login_required
def order_view(request):
    menu_types = MenuType.objects.all()
    allergies = FoodTag.objects.all()

    if request.method == 'POST':
        action = request.POST.get('action')

        # можно выбрать несколько типов меню
        menu_type_ids = request.POST.getlist('foodtype')
        selected_menu_types = MenuType.objects.filter(id__in=menu_type_ids)

        months = int(request.POST.get('months', 1))
        persons = int(request.POST.get('persons', 1))
        breakfast = request.POST.get('breakfast') == '1'
        lunch = request.POST.get('lunch') == '1'
        dinner = request.POST.get('dinner') == '1'
        dessert = request.POST.get('dessert') == '1'
        selected_allergies = request.POST.getlist('allergies')
        promocode = (request.POST.get('promocode') or '').strip()

        # считаем базовую цену и применяем промокод
        base_price = calculate_price(months, persons, breakfast, lunch, dinner, dessert)
        final_price, promo_obj, applied = apply_promocode_if_any(base_price, promocode)

        # "Применить" — просто показать пересчитанную цену и остаться на странице
        if action == 'apply':
            if applied:
                messages.success(request, 'Промокод применён.')
            elif promocode:
                messages.warning(request, 'Промокод не применён.')
            return render(
                request,
                'orders/order.html',
                {
                    'menu_types': menu_types,
                    'allergies': allergies,
                    'price': final_price,
                },
            )

        # "Оплатить" (нужно, чтобы был выбран тип меню)
        if not selected_menu_types.exists():
            messages.warning(request, 'Выберите тип меню.')
            return render(
                request,
                'orders/order.html',
                {
                    'menu_types': menu_types,
                    'allergies': allergies,
                    'price': final_price,
                },
            )

        # профиль пользователя
        user_page, _ = UserPage.objects.get_or_create(
            user=request.user,
            defaults={'username': request.user.username}
        )
        # аллергии
        user_page.allergies.set(FoodTag.objects.filter(id__in=selected_allergies))

        # заменяем прошлую подписку новой
        Subscription.objects.filter(user=user_page).delete()

        # значение для поля промокода (FK или CharField)
        promo_value_for_save = None
        try:
            promo_field = Subscription._meta.get_field('promocode')
            is_fk = isinstance(promo_field, ForeignKey)
        except Exception:
            is_fk = False

        if applied:
            if is_fk:
                promo_value_for_save = promo_obj
            else:
                promo_value_for_save = getattr(promo_obj, "code", None) if promo_obj else (promocode or None)

        # создаём подписку с финальной ценой
        subscription = Subscription.objects.create(
            user=user_page,
            months=months,
            persons=persons,
            breakfast=breakfast,
            lunch=lunch,
            dinner=dinner,
            dessert=dessert,
            price=final_price,
            promocode=promo_value_for_save,
        )

        # привязываем выбранные типы меню к подписке и профилю
        subscription.menu_types.set(selected_menu_types)
        user_page.menu_types.set(selected_menu_types)
        user_page.is_subscribed = True
        user_page.save()

        messages.success(request, 'Подписка успешно оформлена!')
        return redirect('lk')

    # GET
    return render(request, 'orders/order.html', {
        'menu_types': menu_types,
        'allergies': allergies
    })


@login_required
def subscription_recipes_view(request):
    try:
        user_page = UserPage.objects.get(user=request.user)
    except UserPage.DoesNotExist:
        messages.error(request, 'Страница пользователя не найдена')
        return redirect('lk')
    
    active_subscription = user_page.subscription.first()
    
    if not active_subscription:
        messages.warning(request, 'У вас нет активной подписки')
        return redirect('lk')
    
    safe_recipes = user_page.get_safe_recipes()
    
    if active_subscription.menu_types.exists():
        subscription_recipes = safe_recipes.filter(
            menu_types__in=active_subscription.menu_types.all()
        ).distinct()
    else:
        subscription_recipes = safe_recipes
    
    meal_types = []
    if active_subscription.breakfast:
        meal_types.append('breakfast')
    if active_subscription.lunch:
        meal_types.append('lunch')
    if active_subscription.dinner:
        meal_types.append('dinner')
    if active_subscription.dessert:
        meal_types.append('dessert')
    
    if meal_types:
        subscription_recipes = subscription_recipes.filter(meal_type__in=meal_types)
    
    recipes_by_menu_type = {}
    for menu_type in active_subscription.menu_types.all():
        recipes_by_menu_type[menu_type] = subscription_recipes.filter(
            menu_types=menu_type
        )
    
    return render(request, 'accounts/subscription_recipes.html', {
        'user_page': user_page,
        'active_subscription': active_subscription,
        'subscription_recipes': subscription_recipes,
        'recipes_by_menu_type': recipes_by_menu_type,
        'recipes_count': subscription_recipes.count(),
    })


@login_required
def lk_view(request):
    try:
        user_page = UserPage.objects.get(user=request.user)
    except UserPage.DoesNotExist:
        user_page = UserPage.objects.create(
            user=request.user,
            username=request.user.username
        )

    active_subscription = user_page.subscription.first()
    safe_recipes = user_page.get_safe_recipes()

    return render(request, 'accounts/lk.html', {
        'user_page': user_page,
        'active_subscription': active_subscription,
        'safe_recipes_count': safe_recipes.count(),
    })


def calculate_price(months, persons, breakfast, lunch, dinner, dessert):
    prices = {
        1: {'breakfast': 100, 'lunch': 300, 'dinner': 200, 'dessert': 100},
        3: {'breakfast': 200, 'lunch': 600, 'dinner': 400, 'dessert': 200},
        6: {'breakfast': 300, 'lunch': 900, 'dinner': 600, 'dessert': 300},
        12: {'breakfast': 400, 'lunch': 1200, 'dinner': 800, 'dessert': 400}
    }

    month_prices = prices.get(months, prices[1])

    total_price = 0
    if breakfast:
        total_price += month_prices['breakfast']
    if lunch:
        total_price += month_prices['lunch']
    if dinner:
        total_price += month_prices['dinner']
    if dessert:
        total_price += month_prices['dessert']

    total_price *= persons

    return total_price


# --- хелпер применения промокода ---
def apply_promocode_if_any(base_price: int, promocode_raw: str):
    """
    Возвращает (final_price, promo_obj, applied)
    promo_obj — объект PromoCode (если модель есть и код валиден), иначе None.
    applied — True/False, применялась ли скидка.
    """
    promocode_raw = (promocode_raw or "").strip()
    if not promocode_raw:
        return base_price, None, False

    if PromoCode is None:
        return base_price, None, False

    promo = PromoCode.objects.filter(code__iexact=promocode_raw, is_active=True).first()
    if not promo:
        return base_price, None, False

    today = timezone.now().date()
    if hasattr(promo, "valid_from") and promo.valid_from and today < promo.valid_from:
        return base_price, None, False
    if hasattr(promo, "valid_to") and promo.valid_to and today > promo.valid_to:
        return base_price, None, False

    try:
        discount = int(getattr(promo, "discount_percent", 0))
    except Exception:
        discount = 0

    final_price = int(round(base_price * (100 - max(0, min(discount, 100))) / 100))
    return final_price, promo, True


@login_required
def ajax_check_promocode(request):
    """
    GET-параметры:
      promocode, months, persons, breakfast, lunch, dinner, dessert  (значения '1'/'0')
    Возвращает JSON: {applied: bool, final_price: int, discount: int}
    """
    promocode = (request.GET.get("promocode") or "").strip()

    def as_int(name, default):
        try:
            return int(request.GET.get(name, default))
        except Exception:
            return default

    months = as_int("months", 1)
    persons = as_int("persons", 1)
    breakfast = request.GET.get("breakfast", "1") == "1"
    lunch     = request.GET.get("lunch", "1") == "1"
    dinner    = request.GET.get("dinner", "1") == "1"
    dessert   = request.GET.get("dessert", "1") == "1"

    base_price = calculate_price(months, persons, breakfast, lunch, dinner, dessert)
    final_price, promo_obj, applied = apply_promocode_if_any(base_price, promocode)
    discount = int(getattr(promo_obj, "discount_percent", 0)) if applied else 0

    return JsonResponse({
        "applied": applied,
        "final_price": final_price,
        "discount": discount,
    })


def recipe_detail(request, recipe_id):
    try:
        recipe = Recipe.objects.get(id=recipe_id)
        
        if recipe.id % 3 == 1:
            template = 'recipes/card1.html'
        elif recipe.id % 3 == 2:
            template = 'recipes/card2.html'
        else:
            template = 'recipes/card3.html'
        
        return render(request, template, {'recipe': recipe})
        
    except Recipe.DoesNotExist:
        messages.error(request, 'Рецепт не найден')
        return redirect('subscription_recipes')