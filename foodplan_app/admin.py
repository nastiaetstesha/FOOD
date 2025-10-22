from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    User,
    FoodTag,
    Ingredient,
    Recipe,
    RecipeIngredient,
    DailyMenu,
    PriceRange,
    UserPage,
    MenuType,
    Subscription,
)
from django.utils.html import format_html


@admin.register(User)
class UserAdmin(UserAdmin):
    list_display = (
        "username",
        "email",
    )
    list_editable = ("email",)


@admin.register(FoodTag)
class FoodTagAdmin(admin.ModelAdmin):
    list_display = ("name",)



@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        "userpage",
        "menu_type",
        "months",
        "persons",
        "price",
        "breakfast",
        "lunch",
        "dinner",
        "dessert",
    )
    list_filter = ("menu_type", "months", "breakfast", "lunch", "dinner", "dessert")
    list_editable = ("breakfast", "lunch", "dinner", "dessert")
    
    def userpage(self, obj):
        return obj.user.username
    
    userpage.short_description = "Страница пользователя"


class SubscriptionInline(admin.TabularInline):
    model = Subscription
    extra = 0
    fields = ("months", "persons", "price", ("breakfast", "lunch", "dinner", "dessert",))


@admin.register(UserPage)
class UserPageAdmin(admin.ModelAdmin):
    inlines = [
        SubscriptionInline,
    ]
    list_display = (
        "username",
        "user",
        "is_subscribed",
        "menu_type",
        "all_allergies",
        "image_preview",
        "daily_menus",
    )
    list_editable = ("is_subscribed",)
    list_filter = ("is_subscribed",)

    def all_allergies(self, obj):
        if obj.allergies:
            return ", ".join(allergy.name for allergy in obj.allergies.all())
        return "-"

    def daily_menus(self, obj):
        if obj.daily_menu:
            return ", ".join(
                f"{menu.menu_type}-{menu.date}" for menu in obj.daily_menu.all()
            )
        return "-"

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{url}" style="max-width: {max_width}px; max-height: {max_height}px; width: auto; height: auto;"/>',
                max_width=200,
                max_height=200,
                url=obj.image.url,
            )
        return format_html('<span style="color: gray;">Нет изображения</span>')

    image_preview.short_description = "Превью изображения"
    all_allergies.short_description = "Аллергии"
    image_preview.short_description = "Превью изображения"


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    list_display = ("name", "price", "allergens_list")
    list_filter = ("allergens",)
    
    def allergens_list(self, obj):
        if obj.allergens.exists():
            return ", ".join(allergen.name for allergen in obj.allergens.all())
        return "-"
    
    allergens_list.short_description = "Аллергены"

class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 0
    fields = ("ingredient", "mass", "get_allergens")
    autocomplete_fields = ["ingredient"]
    
    def get_allergens(self, obj):
        if obj.ingredient and obj.ingredient.allergens.exists():
            return ", ".join(allergen.name for allergen in obj.ingredient.allergens.all())
        return "-"
    
    get_allergens.short_description = "Аллергены"
    readonly_fields = ['get_allergens']

@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "description",
        "image_preview",
        "meal_type",
        "price",
        "premium",
        "foodtags",
        "allergens_list",  # Добавляем отображение аллергенов
        "on_index",
    ]
    list_filter = ("meal_type", "tags", "premium", "ingredients__ingredient__allergens")
    inlines = [RecipeIngredientInline]
    readonly_fields = ["image_preview"]
    search_fields = ("title",)
    list_editable = ("on_index", "premium")
    
    def allergens_list(self, obj):
        allergens = obj.get_allergens()
        if allergens:
            return ", ".join(allergen.name for allergen in allergens)
        return "-"
    
    allergens_list.short_description = "Аллергены в рецепте"

    def foodtags(self, obj):
        if obj.tags:
            return ", ".join(tag.name for tag in obj.tags.all())
        return "-"

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{url}" style="max-width: {max_width}px; max-height: {max_height}px; width: auto; height: auto; border-radius: 50%"/>',
                max_width=100,
                max_height=100,
                url=obj.image.url,
            )
        return format_html('<span style="color: gray;">Нет изображения</span>')

    image_preview.short_description = "Превью изображения"

@admin.register(MenuType)
class MenuTypeAdmin(admin.ModelAdmin):
    list_display = ("title", "image_preview")

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{url}" style="max-width: {max_width}px; max-height: {max_height}px; width: auto; height: auto;"/>',
                max_width=200,
                max_height=200,
                url=obj.image.url,
            )
        return format_html('<span style="color: gray;">Нет изображения</span>')

    image_preview.short_description = "Превью изображения"


@admin.register(DailyMenu)
class DailyMenuAdmin(admin.ModelAdmin):
    list_display = ("date", "breakfast", "lunch", "dinner", "menu_type")


@admin.register(PriceRange)
class PriceRangeAdmin(admin.ModelAdmin):
    list_display = ["name", "min_price", "max_price"]
    search_fields = ["name"]