from django.shortcuts import render, redirect
from .models import MenuType, FoodTag, UserPage, Subscription
from django.contrib.auth.decorators import login_required

def index(request):
    return render(request, 'index.html')

def auth_view(request):
    return render(request, 'registration/auth.html')

def registration_view(request):
    return render(request, 'registration/registration.html')

def order_view(request):
    menu_types = MenuType.objects.all()
    allergies = FoodTag.objects.all()
    
    if request.method == 'POST':
        menu_type_id = request.POST.get('foodtype')
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
        
        menu_type = MenuType.objects.get(id=menu_type_id)
        subscription = Subscription.objects.create(
            user=user_page,
            menu_type=menu_type,
            months=months,
            persons=persons,
            breakfast=breakfast,
            lunch=lunch,
            dinner=dinner,
            dessert=dessert,
            price=calculate_price(months, persons, breakfast, lunch, dinner, dessert)
        )
        
        return redirect('lk')
    
    return render(request, 'orders/order.html', {
        'menu_types': menu_types,
        'allergies': allergies
    })

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
    base_price = 1000
    price = base_price * months * persons
    
    meals_count = sum([breakfast, lunch, dinner, dessert])
    if meals_count > 1:
        price *= 1.2
    
    return price

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