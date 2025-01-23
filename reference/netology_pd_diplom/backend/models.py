from django.db import models
from django.contrib.auth.validators import UnicodeUsernameValidator
from django_rest_passwordreset.tokens import get_token_generator
from django.contrib.auth.base_user import BaseUserManager
from django.utils.translation import gettext_lazy as _
# Create your models here.

STATE_CHOICES = (
    ('basket', 'Статус корзины'),
    ('new', 'Новый'),
    ('confirmed', 'Подтвержден'),
    ('assembled', 'Собран'),
    ('sent', 'Отправлен'),
    ('delivered', 'Доставлен'),
    ('canceled', 'Отменен'),
    )


USER_TYPE_CHOICES = (
    ('shop', 'Магазин'),
    ('buyer', 'Покупатель'),

)


class UserManager(BaseUserManager):

# Создаем новый экземпляр пользователя
    use_in_migrations = True
    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('Укажите адрес электронной почты')
        email = self.normalize_email(email) 
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self.db)
        return user
        
    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False) 
        return self._create_user(email, password, **extra_fields)


    def _create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        extra_fields.setdefault('is_active', True)
        if extra_fields.get('is_active') is  not True:
            raise ValueError('Superuser must have is_superuser=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self._create_user(email, password, **extra_fields) 
        
#Модель пользователя
class User(models.Model):
    REQUIRED_FIELDS = []
    objects = UserManager()
    USERNAME_FIELDS = 'email'
    email = models.EmailField(_('email address'), unique=True)
    company = models.CharField(verbose_name='Компания', max_length=100, blank=True)
    position = models.CharField(verbose_name='Должность', max_length=100, blank=True)
    username_validator = UnicodeUsernameValidator()
    username = models.CharField(_('username'),  max_length=100, 
                                help_text=("Трбуется не более 100 символов. Буквы, цифры и @/./+/-/_"),
                                validators=[username_validator],
                                error_messages={
                                    'unique': ("Пользователь с таким именем пользователя уже существует"),
                                })
    is_active = models.BooleanField(('active'), help_text = ("Designates whether the user can log into this admin site."), default=False)
    type = models.CharField(verbose_name='Тип пользователя', max_length=100)

    def __str__(self):
        return f'{self.first_name} {self.last_name}'
    
    class Meta:
        verbose_name = 'Пользователь',
        verbose_name_plural = 'Пользователи',
        ordering = ('email',)

class Shop(models.Model):
    objects = models.manager.Manager()
    name = models.CharField(max_length=100)
    user = models.CharField(User, verbose_name='Пользователь', 
                             blank=True, null=True, 
                             on_delete=models.CASCADE)
    url = models.URLField(verbose_name='ССылка', null=True, blank=True)
    state = models.BooleanField(verbose_name='Статус получения заказов', blank=True)

    class Meta:
        verbose_name = 'Магазин'
        verbose_name_plural = "Список магазинов"
        ordering = ('-name',)

    def __str__(self):
        return self.name

class Supplier(models.Model):
    objects = models.manager.Manager()
    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=100)
    phone = models.CharField(max_length=50, help_text=('Enter phone number'))
    supplier_company = models.CharField(verbose_name='Компания', max_length=100, blank=True)
    shops = models.ForeignKey(Shop, verbose_name='Магазины', 
                              related_name='categories', 
                              blank=True, )
    
    class Meta:
        verbose_name = 'Поставщик'
        verbose_name_plural = "Поставщики"
        ordering = ('-name',)

    def __str__(self):
        return self.name
    
class Contact(models.Model):
    objects = models.manager.Manager()
    user = models.CharField(max_length=50, verbose_name='Имя')
    city = models.CharField(max_length=50, verbose_name='Город')
    street = models.CharField(max_length=50, verbose_name='Улица', blank=True)
    house = models.CharField(max_length=50, verbose_name='Дом', blank=True)
    appartmet = models.CharField(max_length=50, verbose_name='Квартира', blank=True)
    phone = models.CharField(max_length=50, verbose_name='Телефон')

    class Meta:
        verbose_name = 'Контакты пользователя'
        verbose_name_plural = "Список контактов пользователя"
        

    def __str__(self):
        return f'{self.city} {self.street} {self.house}'

class Order(models.Model):
    objects = models.manager.Manager()
    user = models.ForeignKey(User, verbose_name='Пользователь', 
                             related_name='contacts',
                             blank=True, 
                             on_delete=models.CASCADE)
    dtime=models.DateTimeField(auto_now_add=True)
    state = models.CharField(verbose_name='Статус', choices=STATE_CHOICES, max_length=30)
    contact = models.CharField(Contact, verbose_name='Контакт', 
                             blank=True, 
                             on_delete=models.CASCADE,
                            null=True)

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = "Список заказов"
        ordering = ('-dtime',)

    def __str__(self):
        return str(self.dt)

class Product(models.Model):
    objects = models.manager.Manager()
    name = models.CharField(max_length=100, verbose_name='Название')
    category = models.CharField(verbose_name='Категория', related_name='products', blank=True)

    class Meta:
        verbose_name = 'Продукты'
        verbose_name_plural = 'Список продуктов'
        ordering = ('-name',)
    
    def __str__(self):
        return self.name

class Category(models.Model):
    objects = models.manager.Manager()
    name = models.ForeignKey(Product, verbose_name='Продукты', 
                             related_name='Categories',
                             blank=True, 
                             on_delete=models.CASCADE)
    
    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = "Список категорий"
        ordering = ('-name',)

    def __str__(self):
        return self.name

class Parametr(models.Model):
    objects = models.manager.Manager()
    name = models.CharField(max_length=50, verbose_name='Имя')

    class Meta:
        verbose_name = 'Имя параметра'
        verbose_name_plural = "Список имен параметров"
        ordering = ('-name',)

    def __str__(self):
        return self.name

class InfoProduct(models.Model):
    objects = models.manager.Manager()
    model = models.CharField(max_length=100, verbose_name='Модель', blank=True)
    appearence = models.PositiveBigIntegerField(verbose_name='Внешний вид')
    shop = models.ForeignKey(Shop, verbose_name='Магазин', 
                             related_name='product_info', 
                             blank=True, 
                             on_delete=models.CASCADE)
    product = models.ForeignKey(Product, verbose_name='Продукт', 
                                related_name='', 
                                blank=True,
                                on_delete=models.CASCADE)
    quantiti = models.PositiveBigIntegerField(verbose_name='Количество')
    price = models.PositiveBigIntegerField(verbose_name='Цена')
    price_rss = models.PositiveBigIntegerField(verbose_name='Рекомендуемая розничная цена')

    class Meta:
            verbose_name = 'Информация о продукте'
            verbose_name_plural = "Информация о продуктах"
            constraints = [
                models.UniqueConstraint(fields=['product', 'shop', 'appearence'], name='unique_product_info'),
            ]

class ProductParametr(models.Models):
    objects = models.manager.Manager()
    parametr = models.ForeignKey(Parametr, verbose_name='Параметры', 
                                 related_name='Параметры продукта', 
                                 blank=True, 
                                 on_delete=models.CASCADE)
    inforpoduct = models.ForeignKey(InfoProduct, verbose_name='Информация', 
                                 related_name='Информация о продукте', 
                                 blank=True, 
                                 on_delete=models.CASCADE)

class OrderItem(models.Model):
    objects = models.manager.Manager()
    order = models.ForeignKey(Order, verbose_name='Заказ',
                              blank=True,
                              on_delete=models.CASCADE)
    info_product = models.ForeignKey(InfoProduct, verbose_name='Информация о продукте',
                                     blank=True,
                                     on_delete=models.CASCADE)
    value = models.CharField(verbose_name='Значение', max_length=50)


    class Meta:
        verbose_name = 'Заказанная позиция'
        verbose_name_plural = "Список заказанных позиций"
        constraint = [
            models.UniqueConstraint(fields=['order_id', 'info_product'], name='unique_order_item')
        ]
        
class ConfirmEmailToken(models.Model):
    object = models.manager.Manager()
    class Meta:
        verbose_name = "Токен подтверждения email"
        verbose_name_plural = "Токен подтверждения email"
    
    @staticmethod
    def generate_key():
        return get_token_generator().generate_token()

    user = models.ForeignKey(User, related_name='confirm_email_token', 
                             on_delete=models.CASCADE, 
                             verbose_name=("The User which is associated to this password reset token"))
    create_at = models.DateTimeField(auto_now_add=True,
                                     verbose_name=("When was this token generated"))
    key = models.CharField(("Key"), max_length=100, db_index=True, unique=True)

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = self.generate_key()
        return super(ConfirmEmailToken,  self).save(**args, **kwargs)
    def __str__(self):
        return "Password reset token for user{user}".format(user=self.user)
