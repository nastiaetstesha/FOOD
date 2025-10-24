from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Q


class User(AbstractUser):
    email = models.EmailField(unique=True)

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"


class FoodTag(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Аллерген"
        verbose_name_plural = "Аллергены"


class PriceRange(models.Model):
    name = models.CharField(
        max_length=100,
        verbose_name="Название диапазона (например, 'До 1 000 руб')",
        unique=True,
    )
    min_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Минимальная цена",
    )
    max_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Максимальная цена",
    )

    def get_name(self):
        if self.min_price and self.max_price:
            return f"От {int(self.min_price)} до {int(self.max_price)} руб."
        elif self.min_price:
            return f"От {int(self.min_price)} руб."
        elif self.max_price:
            return f"До {int(self.max_price)} руб."
        return

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.name:
            self.name = self.get_name()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Диапазон цен"
        verbose_name_plural = "Диапазоны цен"


class Ingredient(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(
        verbose_name="Стоимость, руб./ 100 г",
        max_digits=10,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0)],
    )

    caloricity = models.DecimalField(
        verbose_name="Калорийность, ккал/100 г",
        max_digits=10,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0)],
    )
    
    allergens = models.ManyToManyField(
        FoodTag, 
        related_name="ingredients", 
        verbose_name="Аллергены",
        blank=True
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"


class MenuType(models.Model):
    title = models.CharField(max_length=255, unique=True, verbose_name="Тип меню")
    image = models.ImageField(
        upload_to="menus/",
        verbose_name="Изображение меню",
        blank=True,
        null=True,
    )

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Тип меню"
        verbose_name_plural = "Типы меню"


class Recipe(models.Model):
    MEAL_TYPES = [
        ("breakfast", "Завтрак"),
        ("lunch", "Обед"),
        ("dinner", "Ужин"),
        ("dessert", "Десерт"),
    ]

    title = models.CharField(max_length=255, unique=True, verbose_name="Название блюда")
    image = models.ImageField(verbose_name="Изображение", upload_to="recipes/")
    description = models.TextField(blank=True, verbose_name="Описание")
    sequence = models.TextField(blank=True, verbose_name="Пошаговая инструкция")
    meal_type = models.CharField(
        max_length=20,
        choices=MEAL_TYPES,
        verbose_name="Прием пищи",
        default="breakfast",
    )
    premium = models.BooleanField(
        default=False, verbose_name="Для премиум-пользователей"
    )

    on_index = models.BooleanField(
        default=False, verbose_name="Отображать на главной странице?"
    )

    price = models.DecimalField(
        verbose_name="Итоговая стоимость, руб.",
        max_digits=10,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0)],
    )
    mass = models.DecimalField(
        verbose_name="Масса, г.",
        max_digits=10,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0)],
    )
    calories = models.DecimalField(
        verbose_name="Общая калорийность, ккал",
        max_digits=10,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0)],
    )

    menu_types = models.ManyToManyField(
        MenuType,
        verbose_name="Типы меню",
        related_name="recipes",
        blank=True
    )

    def get_price(self):
        price = 0
        for ingredient in self.ingredients.all():
            if ingredient.ingredient.price and ingredient.mass:
                price += ingredient.ingredient.price * ingredient.mass / 100
        return price

    def get_mass(self):
        mass = 0
        for ingredient in self.ingredients.all():
            if ingredient.mass:
                mass += ingredient.mass
        return mass

    def get_calories(self):
        calories = 0
        for ingredient in self.ingredients.all():
            if ingredient.ingredient.caloricity and ingredient.mass:
                calories += ingredient.mass * ingredient.ingredient.caloricity / 100
        return calories

    def get_allergens(self):
        allergens = set()
        for ingredient in self.ingredients.all():
            allergens.update(ingredient.ingredient.allergens.all())
        return list(allergens)

    def has_user_allergies(self, user_allergies):
        recipe_allergens = self.get_allergens()
        user_allergy_ids = [allergy.id for allergy in user_allergies]
        recipe_allergen_ids = [allergen.id for allergen in recipe_allergens]
        
        return bool(set(user_allergy_ids) & set(recipe_allergen_ids))

    def is_safe_for_user(self, user_page):
        if not user_page.allergies.exists():
            return True
        return not self.has_user_allergies(user_page.allergies.all())

    def __str__(self):
        return f'{self.title}{" - Премиум" if self.premium else ""}'

    class Meta:
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name="ingredients"
    )
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    mass = models.DecimalField(
        verbose_name="Масса в г",
        max_digits=10,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0)],
    )

    def __str__(self):
        return f"{self.recipe.title}: {self.ingredient.name}, {self.mass} г"

    class Meta:
        verbose_name = "Ингредиент рецепта"
        verbose_name_plural = "Ингредиенты рецептов"


class UserPage(models.Model):
    username = models.CharField(
        max_length=255, verbose_name="Имя", blank=True, default="Имя"
    )

    image = models.ImageField(
        upload_to="avatars/", verbose_name="Изображение", blank=True, null=True
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="page",
        verbose_name="Связанный аккаунт",
    )
    is_subscribed = models.BooleanField(default=False, verbose_name="Премиум")

    allergies = models.ManyToManyField(
        FoodTag, related_name="userpages", verbose_name="Аллергии", blank=True
    )
    liked_recipes = models.ManyToManyField(
        Recipe, related_name="liked", verbose_name="Понравившиеся рецепты", blank=True
    )
    disliked_recipes = models.ManyToManyField(
        Recipe,
        related_name="disliked",
        verbose_name="Непонравившиеся рецепты",
        blank=True,
    )

    menu_types = models.ManyToManyField(
        MenuType,
        related_name="users",
        verbose_name="Типы меню",
        blank=True,
    )

    def get_active_subscription(self):
        return self.subscription.first()
    
    def has_active_subscription(self):
        return self.subscription.exists()

    def get_safe_recipes(self):
        if self.menu_types.exists():
            base_recipes = Recipe.objects.filter(menu_types__in=self.menu_types.all()).distinct()
        else:
            base_recipes = Recipe.objects.all()
        if not self.allergies.exists():
            return base_recipes
        safe_recipes = base_recipes
        for allergy in self.allergies.all():
            safe_recipes = safe_recipes.exclude(
                ingredients__ingredient__allergens=allergy
            )
        return safe_recipes.distinct()

    def __str__(self):
        return self.username

    class Meta:
        verbose_name = "Страница клиента"
        verbose_name_plural = "Страницы клиентов"
        ordering = ["username"]

# def get_safe_recipes(self):
    
#     conditions = Q()
    
#     if self.menu_types.exists():
#         conditions &= Q(menu_types__in=self.menu_types.all())
    
#     if self.allergies.exists():
#         for allergy in self.allergies.all():
#             conditions &= ~Q(ingredients__ingredient__allergens=allergy)
    
#     return Recipe.objects.filter(conditions).distinct()

# def __str__(self):
#     return self.username

class Meta:
    verbose_name = "Страница клиента"
    verbose_name_plural = "Страницы клиентов"
    ordering = ["username"]


class PromoCode(models.Model):
    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Код промокода"
    )
    discount_percent = models.PositiveIntegerField(
        default=0,
        verbose_name="Скидка (%)"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Активен"
    )
    valid_from = models.DateField(
        null=True,
        blank=True,
        verbose_name="Действует с"
    )
    valid_to = models.DateField(
        null=True,
        blank=True,
        verbose_name="Действует до"
    )

    def __str__(self):
        return f"{self.code} (-{self.discount_percent}%)"

    class Meta:
        verbose_name = "Промокод"
        verbose_name_plural = "Промокоды"


class Subscription(models.Model): 
    base_price = models.DecimalField(
        verbose_name="Базовая стоимость подписки, руб",
        max_digits=10,
        decimal_places=2,
        default=1000.00,
        validators=[MinValueValidator(0)],
    )

    user = models.ForeignKey(
        UserPage,
        related_name="subscription",
        on_delete=models.CASCADE,
        verbose_name="Пользователь",
    )
    
    menu_types = models.ManyToManyField(
        MenuType,
        related_name="subscriptions",
        verbose_name="Типы меню",
        blank=True,
    )

    months = models.PositiveIntegerField(
        verbose_name="Количество месяцев",
        validators=[
            MinValueValidator(1, message="Минимальный срок - 1 месяц"),
            MaxValueValidator(12, message="Максимальный срок - 12 месяцев (1 год)"),
        ],
        default=1,
    )
    persons = models.PositiveIntegerField(
        verbose_name="Количество персон",
        validators=[
            MinValueValidator(1, message="Минимум - 1 персона"),
            MaxValueValidator(5, message="Максимум - 5 персон"),
        ],
        default=1,
    )

    breakfast = models.BooleanField(verbose_name="Завтраки", default=True)
    lunch = models.BooleanField(verbose_name="Обеды", default=False)
    dinner = models.BooleanField(verbose_name="Ужины", default=False)
    dessert = models.BooleanField(verbose_name="Десерты", default=False)
    
    price = models.DecimalField(verbose_name="Стоимость, руб.",
        max_digits=10,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0)],
    )

    promocode = models.ForeignKey(
        PromoCode,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name="Промокод",
        related_name="subscriptions"
    )


    class Meta:
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        ordering = ["user"]
    

class DailyMenu(models.Model):
    DAYS_OF_WEEK = [
        ("mon", "понедельник"),
        ("tue", "вторник"),
        ("wen", "среда"),
        ("thu", "четверг"),
        ("fri", "пятница"),
        ("sat", "суббота"),
        ("sun", "воскресенье"),
    ]

    menu_types = models.ManyToManyField(
        MenuType,
        related_name="dailymenus",
        verbose_name="Типы меню",
        blank=True,
    )

    date = models.CharField(
        max_length=3,
        choices=DAYS_OF_WEEK,
        verbose_name="День недели",
        default="mon",
    )

    breakfast = models.ForeignKey(
        Recipe,
        on_delete=models.SET_NULL,
        null=True,
        related_name="breakfast_menus",
    )
    lunch = models.ForeignKey(
        Recipe, on_delete=models.SET_NULL, null=True, related_name="lunch_menus"
    )
    dinner = models.ForeignKey(
        Recipe, on_delete=models.SET_NULL, null=True, related_name="dinner_menus"
    )

    dessert = models.ForeignKey(
        Recipe, on_delete=models.SET_NULL, null=True, related_name="dessert_menus"
    )

    users = models.ManyToManyField(
        UserPage, verbose_name="Пользователи", related_name="daily_menu", blank=True
    )

    def get_safe_menu_for_user(self, user_page):
        safe_menu = {
            'breakfast': self.breakfast,
            'lunch': self.lunch,
            'dinner': self.dinner,
            'dessert': self.dessert,
        }
        
        for meal_type, recipe in safe_menu.items():
            if recipe and not recipe.is_safe_for_user(user_page):
                replacement = user_page.get_safe_recipes().filter(
                    meal_type=recipe.meal_type,
                    menu_types__in=user_page.menu_types.all()
                ).first()
                safe_menu[meal_type] = replacement
        
        return safe_menu

    def __str__(self):
        return f"Меню на {self.date}"

    class Meta:
        verbose_name = "Дневное меню"
        verbose_name_plural = "Дневные меню"
