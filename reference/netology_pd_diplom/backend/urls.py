from django.urls import path
from django_rest_passwordreset.views import reset_password_confirm, reset_password_request_token
from backend.views import CategoryView, RegisterAccount, ConfirmAccount, AccountDetails, LoginAccount, InfoProductView, BasketView, OrderView




app_name = 'backend'
urlpatterns = [
    path('user/password_rest', reset_password_request_token, name='password-reset'),
    path('user/password_rest/confirm', reset_password_confirm, name='password-reset-confirm'),
    path('user/register', RegisterAccount.as_view, name='user-register'),
    path('user/register/confirm', ConfirmAccount.as_view, name='user-register-confirm'),
    path('user/details', AccountDetails.as_view, name='user-details'),
    path('user/login', LoginAccount.as_view, name='user-login'),
    path('categories', CategoryView.as_view(), name='categories'),
    path('products', InfoProductView.as_view(), name='shop'),
    path('basket', BasketView.as_view(), name='basket'),
    path('order', OrderView.as_view(), name='order'),
]