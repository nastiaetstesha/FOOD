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
    PromoCode,
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
        "menu_types_list",
        "months",
        "persons",
        "price",
        "breakfast",
        "lunch",
        "dinner",
        "dessert",
    )
    list_filter = ("months", "breakfast", "lunch", "dinner", "dessert")
    list_editable = ("breakfast", "lunch", "dinner", "dessert")
    filter_horizontal = ("menu_types",)
    
    def userpage(self, obj):
        return obj.user.username
    
    def menu_types_list(self, obj):
        if obj.menu_types.exists():
            return ", ".join(menu_type.title for menu_type in obj.menu_types.all())
        return "-"
    
    userpage.short_description = "Страница пользователя"
    menu_types_list.short_description = "Типы меню"


class SubscriptionInline(admin.TabularInline):
    model = Subscription
    extra = 0
    fields = ("menu_types", "months", "persons", "price", ("breakfast", "lunch", "dinner", "dessert",))
    filter_horizontal = ("menu_types",)


@admin.register(UserPage)
class UserPageAdmin(admin.ModelAdmin):
    inlines = [
        SubscriptionInline,
    ]
    list_display = (
        "username",
        "user",
        "is_subscribed",
        "menu_types_list",
        "all_allergies",
        "image_preview",
        "daily_menus",
    )
    list_editable = ("is_subscribed",)
    list_filter = ("is_subscribed", "menu_types")
    filter_horizontal = ("menu_types", "allergies", "liked_recipes", "disliked_recipes")

    def menu_types_list(self, obj):
        if obj.menu_types.exists():
            return ", ".join(menu_type.title for menu_type in obj.menu_types.all())
        return "-"
    
    menu_types_list.short_description = "Типы меню"

    def all_allergies(self, obj):
        if obj.allergies:
            return ", ".join(allergy.name for allergy in obj.allergies.all())
        return "-"

    def daily_menus(self, obj):
        if obj.daily_menu:
            return ", ".join(
                f"{menu.date}" for menu in obj.daily_menu.all()
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


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    list_display = ("name", "price", "allergens_list")
    list_filter = ("allergens",)
    filter_horizontal = ("allergens",)
    
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
        "allergens_list",
        "menu_types_list",
        "on_index",
    ]
    list_filter = ("meal_type", "premium", "ingredients__ingredient__allergens", "menu_types")
    inlines = [RecipeIngredientInline]
    readonly_fields = ["image_preview"]
    search_fields = ("title",)
    list_editable = ("on_index", "premium")
    filter_horizontal = ("menu_types",)
    
    def allergens_list(self, obj):
        allergens = obj.get_allergens()
        if allergens:
            return ", ".join(allergen.name for allergen in allergens)
        return "-"
    
    def menu_types_list(self, obj):
        if obj.menu_types.exists():
            return ", ".join(menu_type.title for menu_type in obj.menu_types.all())
        return "-"
    
    allergens_list.short_description = "Аллергены в рецепте"
    menu_types_list.short_description = "Типы меню"

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
    list_display = ("date", "breakfast", "lunch", "dinner", "menu_types_list")
    filter_horizontal = ("menu_types", "users")

    def menu_types_list(self, obj):
        if obj.menu_types.exists():
            return ", ".join(menu_type.title for menu_type in obj.menu_types.all())
        return "-"
    
    menu_types_list.short_description = "Типы меню"


@admin.register(PriceRange)
class PriceRangeAdmin(admin.ModelAdmin):
    list_display = ["name", "min_price", "max_price"]
    search_fields = ["name"]


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_percent', 'is_active', 'valid_from', 'valid_to')
    list_filter = ('is_active',)
    search_fields = ('code',)