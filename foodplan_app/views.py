from django.shortcuts import render, redirect
from .models import MenuType, FoodTag, UserPage, Subscription
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout

from django.utils import timezone
try:
    from .models import PromoCode   # если модели нет — продолжит работать без скидки
except Exception:
    PromoCode = None
from django.db.models.fields.related import ForeignKey


def index(request):
    return render(request, 'index.html')

def auth_view(request):
    return render(request, 'registration/auth.html')

def registration_view(request):
    return render(request, 'registration/registration.html')

# @login_required
# def order_view(request):
#     menu_types = MenuType.objects.all()
#     allergies = FoodTag.objects.all()
    
#     if request.method == 'POST':
#         menu_type_ids = request.POST.getlist('foodtype')  # ИЗМЕНИТЬ: getlist для множественного выбора
#         months = int(request.POST.get('months', 1))
#         persons = int(request.POST.get('persons', 1))
#         breakfast = request.POST.get('breakfast') == '1'
#         lunch = request.POST.get('lunch') == '1'
#         dinner = request.POST.get('dinner') == '1'
#         dessert = request.POST.get('dessert') == '1'
#         selected_allergies = request.POST.getlist('allergies')
#         user_page, created = UserPage.objects.get_or_create(
#             user=request.user,
#             defaults={'username': request.user.username}
#         )
        
#         user_page.allergies.set(FoodTag.objects.filter(id__in=selected_allergies))
        
#         Subscription.objects.filter(user=user_page).delete()
        
#         subscription = Subscription.objects.create(
#             user=user_page,
#             months=months,
#             persons=persons,
#             breakfast=breakfast,
#             lunch=lunch,
#             dinner=dinner,
#             dessert=dessert,
#             price=calculate_price(months, persons, breakfast, lunch, dinner, dessert)
#         )
        
#         selected_menu_types = MenuType.objects.filter(id__in=menu_type_ids)
#         subscription.menu_types.set(selected_menu_types)
        
#         user_page.menu_types.set(selected_menu_types)
#         user_page.is_subscribed = True
#         user_page.save()
        
#         return redirect('lk')
    
#     return render(request, 'orders/order.html', {
#         'menu_types': menu_types,
#         'allergies': allergies
#     })


@login_required
def order_view(request):
    menu_types = MenuType.objects.all()
    allergies = FoodTag.objects.all()

    if request.method == 'POST':
        action = request.POST.get('action')

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

        # --- НОВОЕ: считаем базовую цену и применяем промокод ---
        base_price = calculate_price(months, persons, breakfast, lunch, dinner, dessert)
        final_price, promo_obj, applied = apply_promocode_if_any(base_price, promocode)

        # Если пользователь нажал "Применить" — просто показать пересчитанную цену и остаться на странице
        if action == 'apply':
            return render(
                request,
                'orders/order.html',
                {
                    'menu_types': menu_types,
                    'allergies': allergies,
                    'price': final_price,
                },
            )

        # Дальше — "Оплатить"
        if not selected_menu_types.exists():
            return render(
                request,
                'orders/order.html',
                {
                    'menu_types': menu_types,
                    'allergies': allergies,
                    'error': 'Выберите тип меню',
                    'price': final_price,
                },
            )

        # профиль пользователя
        user_page, _ = UserPage.objects.get_or_create(
            user=request.user,
            defaults={'username': request.user.username},
        )

        # аллергии
        user_page.allergies.set(FoodTag.objects.filter(id__in=selected_allergies))

        # заменяем прошлую подписку новой
        Subscription.objects.filter(user=user_page).delete()

        promo_field = Subscription._meta.get_field('promocode')
        is_fk = isinstance(promo_field, ForeignKey)

        promo_value_for_save = None
        if applied:
            if is_fk:
                promo_value_for_save = promo_obj
            else:
                promo_value_for_save = getattr(promo_obj, "code", None) if promo_obj else (promocode or None)

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

        # отметить выбранное меню у профиля
        subscription.menu_types.set(selected_menu_types)
        user_page.menu_types.set(selected_menu_types)
        user_page.is_subscribed = True
        user_page.save()

        return redirect('lk')

    return render(
        request,
        'orders/order.html',
        {
            'menu_types': menu_types,
            'allergies': allergies,
        },
    )



@login_required
def lk_view(request):
    user_page, created = UserPage.objects.get_or_create(
        user=request.user,
        defaults={'username': request.user.username}
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


# --- добавлено: хелпер применения промокода ---
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


def recipe_detail(request, recipe_id):
    if recipe_id == 1:
        template = 'recipes/card1.html'
    elif recipe_id == 2:
        template = 'recipes/card2.html'
    elif recipe_id == 3:
        template = 'recipes/card3.html'
    else:
        template = 'recipes/card1.html'
    
    return render(request, template, {'recipe_id': recipe_id})


def logout_view(request):
    logout(request)
    return redirect('index')