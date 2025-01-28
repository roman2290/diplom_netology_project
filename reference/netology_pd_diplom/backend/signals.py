from django.dispatch import receiver, Signal
from django_rest_passwordreset.signals import reset_password_token_created
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.db.models.signals import post_save
from models import User, ConfirmEmailToken
from typing import Type

new_user_regestered = Signal()

new_order = Signal()


@receiver(reset_password_token_created)
def password_reset_token_created(sender, instace, reset_password_token, **kwargs):
    #Отправляем письмо токеным для сбоса пароля
    msg = EmailMultiAlternatives(
        f"Password Reset Token for {reset_password_token.user}",
        reset_password_token.key,
        settings.EMAIL_HOST_USER,
        [reset_password_token.user.email]
    )
    msg.send



#Отправляем письмо с подтверждением почты
@receiver(post_save, sender=User)
def new_user_registered_signal(sender: Type[User], instance: User, created: bool, **kwargs):
    if created and not instance.is_active:
        token, _ = ConfirmEmailToken.object.get_or_create(user_id=instance.pk)
        msg = EmailMultiAlternatives(
            f"Password Reset Token for {instance.user}",
            token.key,
            settings.EMAIL_HOST_USER,
            [instance.email]
        )
        msg.send



# ОТправляем письмо при изменении заказа
@receiver(new_order)
def new_order_signal(user_id, **kwargs):
    user = User.objects.get(id=user_id)
    msg = EmailMultiAlternatives(
            f"Обновление статуса заказа"
            'Заказ сформирован',
            settings.EMAIL_HOST_USER,
            [user.email]
        )
    msg.send