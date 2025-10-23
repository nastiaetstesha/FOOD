from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from foodplan_app.views import index, order_view, lk_view, recipe_detail


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index, name='index'),

    # логин/логаут
    path('auth/', auth_views.LoginView.as_view(template_name='registration/auth.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='index'), name='logout'),

    path('registration/', auth_views.LoginView.as_view(template_name='registration/registration.html'), name='registration'),  # временно
    path('order/', order_view, name='order'),
    path('lk/', lk_view, name='lk'),
    path('recipes/<int:recipe_id>/', recipe_detail, name='recipe_detail'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
