from django.shortcuts import render

def index(request):
    return render(request, 'index.html')

def auth_view(request):
    return render(request, 'registration/auth.html')

def registration_view(request):
    return render(request, 'registration/registration.html')

def order_view(request):
    return render(request, 'orders/order.html')

def lk_view(request):
    return render(request, 'accounts/lk.html')

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