from django.contrib import admin
from django.urls import path
from foodplan_app.views import *
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index, name='index'),
    path('auth/', auth_view, name='auth'),
    path('registration/', registration_view, name='registration'),
    path('order/', order_view, name='order'),
    path('lk/', lk_view, name='lk'),
    path('recipes/<int:recipe_id>/', recipe_detail, name='recipe_detail'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)