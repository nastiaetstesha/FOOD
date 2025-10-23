from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import MenuType, FoodTag, UserPage, Subscription, User
from .forms import EmailAuthenticationForm, CustomUserCreationForm


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
            
            UserPage.objects.create(
                user=user,
                username=user.username
            )
            
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
        menu_type_ids = request.POST.getlist('foodtype')
        months = int(request.POST.get('months', 1))
        persons = int(request.POST.get('persons', 1))
        breakfast = request.POST.get('breakfast') == '1'
        lunch = request.POST.get('lunch') == '1'
        dinner = request.POST.get('dinner') == '1'
        dessert = request.POST.get('dessert') == '1'
        selected_allergies = request.POST.getlist('allergies')
        
        user_page, created = UserPage.objects.get_or_create(
            user=request.user,
            defaults={'username': request.user.username}
        )
        
        user_page.allergies.set(FoodTag.objects.filter(id__in=selected_allergies))
        
        Subscription.objects.filter(user=user_page).delete()
        
        subscription = Subscription.objects.create(
            user=user_page,
            months=months,
            persons=persons,
            breakfast=breakfast,
            lunch=lunch,
            dinner=dinner,
            dessert=dessert,
            price=calculate_price(months, persons, breakfast, lunch, dinner, dessert)
        )
        
        selected_menu_types = MenuType.objects.filter(id__in=menu_type_ids)
        subscription.menu_types.set(selected_menu_types)
        
        user_page.menu_types.set(selected_menu_types)
        user_page.is_subscribed = True
        user_page.save()
        
        messages.success(request, 'Подписка успешно оформлена!')
        return redirect('lk')
    
    return render(request, 'orders/order.html', {
        'menu_types': menu_types,
        'allergies': allergies
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