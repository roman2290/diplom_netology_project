from django.shortcuts import render
from models import User, Shop, Category, Order, OrderItem, Supplier, Contact, Product, InfoProduct, ProductParametr, ConfirmEmailToken
from django.contrib.auth.password_validation import validate_password
from django.http import JsonResponse
from serializers import UserSerializer
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from django.contrib.auth import authenticate
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.db.models import Q, Sum, F
from ujson import loads as load_json
from django.db import IntegrityError
from backend.signals import new_order
from serializers import OrderSerializer, ContactSerializer, CategorySerializer, ShopSerializer, ProductSerializer, ProductParametrSerializer, InfoProductSerializer, OrderItemSerializer


# Create your views here.




# Регистрация покупателя

class RegisterAccount(APIView):
    def post(self, request, *args, **kwargs):

        # Проврка на наличие необходимых аргументов

        if {'first_name', 'last_name', 'email', 'password', 'company', 'position'}.issubset(request.data):
            
            # Проверка пароля на сложность
            sad = 'asd'
            try:
                validate_password(request.data['password'])
            except Exception as password_error:
                error_array = []
                for item in password_error:
                    error_array.append(item)
                return JsonResponse({'Satus': False, 'Errors': {'password': error_array}})
            # проверка уникальности имени пользователя
            else:
                user_serializer = UserSerializer(data = request.data)
                if user_serializer.is_valid():
                    user = user_serializer.save()
                    user.set_password(request.data['password'])
                    user.save()
                    return JsonResponse({'Status': True})
                else:
                    return JsonResponse({'Status': False, 'Errors': user_serializer.errors})
        return ({'Status': False, 'Errors': 'Все необходимые аргументы не указаны'})
        



# Подтверждение почтвого адреса
class ConfirmAccount(APIView):

    def post(self, request, *args, **kwargs):

    # Подтверждение почтвого адреса
        if {'email', 'token'}.issubset(request.data):
            token  = ConfirmEmailToken.objects.filter(user__email = request.data['email'], key = request.data['token']).first

            if token:
                token.user.is_active = True
                token.user.save()
                token.delete()
                return JsonResponse({'Status': True})
            else:
                return JsonResponse({'Status': False, 'Errors': 'Не правиль указан токеи и email'})
        return ({'Status': False, 'Errors': 'Все необходимые аргументы не указаны'})


# Управление учетной записью пользователя

class AccountDetails(APIView):

    # Получить данные
    def get(self, request: Request, *args, **kwargs):
        if not request.user.is_authenticate:
            return JsonResponse({'Status': False, 'Error': 'Требуется войтив систему'}, status = 403)
        serealizer = UserSerializer(request.user)
        return Response(serealizer.data)


# Обновление данных учетной записи польззователя
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticate:
            return JsonResponse({'Status': False, 'Error': 'Требуется войтив систему'}, status = 403)
        
        
        # Проверка обязательных аргументов

        if 'password' in request.date:
            error = {}
            try:
                validate_password(request.data['password'])
            except Exception as password_error:
                error_array = []
                for item in password_error:
                    error_array.append(item)
                return JsonResponse({'Status': False, 'Errors': {'password': error_array}})
            else:
                request.user.set_password(request.data['password'])
        

        #проверка данных
        user_serializer = UserSerializer(request.user, data=request.data, patrial=False)
        if user_serializer.is_valid:
            user_serializer.save()
            return JsonResponse({'Status': True})
        else:
            return JsonResponse({'Status': False, 'Errors': user_serializer.errors})



# Автооризация пользователя

class LoginAccount(APIView):

    def post(self, request, *args, **kwargs):
        if {'email', 'password'}.issubset(request.data):
            user = authenticate(request, username=request.data['email'], password=request.data['password'])
            if user is not None:
                if user.is_active: 
                    token, _ = Token.objects.get_or_create(user=user)
                    return JsonResponse({'Status': True, 'Token': token.key})

            return JsonResponse({'Status': False, 'Errors': 'Не удалось авторизовать'})

        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})


# Просмотр категорий
class CategoryView(ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    

# Просмотр списка магазинов
class ShopView(ListAPIView):
    queryset = Shop.objects.filter(state=True)
    serializer_class = ShopSerializer

# Поиск продуктов
class InfoProductView(APIView):

    #Получение списка продуктов
    def get(self, request: Request, *args, **kwargs):
        query = Q(shop__state = True)
        shop_id = request.query_params.get('shop_id')
        category_id = request.query_params.get('category_id')

        if shop_id:
            query= query & Q(shop_id=shop_id)
        
        if category_id:
            query= query & Q(product__category_id=category_id)
        
        queryset = InfoProduct.objects.filter(query).select_related('shop', 
                                    'product__category').prefetch_related('product_parameters__parameter').distinct()
        
        serializer = InfoProductSerializer(queryset, many=True)
        return(serializer.data)

# Управление корзиной покупок

class BasketView(APIView):
    
    
    # Получить корзину
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Требуется войти в систему'}, status=403)
        bascket = Order.objects.filter(user_id = request.user.id, state='basket').prefetch_related('ordered_items__product_info__category', 
                                        'order_items__product_info__product__category', 'ordered_items__product_info__product_parameters__parametr'
                                        ).annotate(total_sum=Sum(F('ordered_items__quantity') * F('ordered_items__product_info__price'))).distinct()
        serializer = OrderItem(bascket, many=True)
        return Response(serializer.data)

        
        # Добавить товар в корзину
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Требуется войти в систему'}, status=403)
        items_add = request.data.get('items')
        if items_add:
            try:
                items_dict = load_json(items_add)
            except ValueError:
                return JsonResponse({'Status': False, 'Errors': 'Неверный формат запроса'})
            else:
                basket, _ = Order.objects.get_or_create(user_id=request.user.id, state='basket')

                object_created = 0

                for order_item in items_dict:
                    order_item.update({'order': basket.id})
                    serializer = OrderItemSerializer(data=order_item)
                    if serializer.isvalid():
                        try:
                            serializer.save()
                        except IntegrityError as error:
                            return JsonResponse({'Status': False, 'Errors': str(error)})
                        else:
                            object_created += 1 
                    else:
                        return JsonResponse({'Status': False, 'Errors': object_created})
                return JsonResponse({'Status': True, 'Создано объектов': serializer.errors})
        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})
                    


    # Удалить товар из корзины
    def delete(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Требуется войти в систему'}, status=403)
        
        items_sting = request.data.get('items')
        if items_sting:
            items_list = items_sting.split(',')
            basket, _ = Order.objects.get_or_create(user_id=request.user.id, state='basket')
            query = Q
            objects_deleted = False
            for order_item_id in items_list:
                if order_item_id.isdigit():
                    query = query | Q(order_id=basket.id, id = order_item_id)
                    objects_deleted = True
            if objects_deleted:
                delete_count = OrderItem.objects.filter(query).delete()[0]
                return JsonResponse({'Status': True, 'Удалено объектов': delete_count})
            return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})
        
    #Добавление позиции в корзину
    def put(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Требуется войти в систему'}, status=403)
        
        items_sting = request.data.get('item')
        if items_sting:
            try:
                items_dict = load_json(items_sting)
            except ValueError:
                return JsonResponse({'Status': False, 'Errors': 'Неверный формат запроса'})
            else:
                basket, _ = Order.objects.get_or_create(user_id=request.user.id, state='basket')

                objects_update = 0
                for order_item in items_dict:
                    if type(order_item['id']) == int and type(order_item['quntity']) == int:
                        objects_update += OrderItem.objects.filter(order_id=basket.id, id = order_item['id']).update(quantit=order_item['quantity'])
                return JsonResponse({'Status': True, 'Обнавлено объектов': objects_update})
        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})


class ContactView(APIView):
    
    # Получить мои контакты
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Требуется войти в систему'}, status=403)
        contact = Contact.objects.filter(user_id = request.user.id)
        serializer = ContactSerializer(contact, many=True)
        return Response(serializer.data)


    # Добавить новый контакт
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Требуется войти в систему'}, status=403)
        if {'city', 'street', 'house'}.issubset(request.data):
            request.data._mutable = True
            request.data.update({'Status': request.user.id})
            serializer = ContactSerializer(data=request.data)
        
            if serializer.is_valid():
                serializer.save()
                return JsonResponse({'Status': True})
            else:
                return JsonResponse({'Status': False, 'Error': serializer.errors})
        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})


    # Удалить контакт
    def delete(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Требуется войти в систему'}, status=403)
        
        items_sting = request.data.get('items')
        if items_sting:
            items_list = items_sting.split(',')
            query = Q
            objects_deleted = False
            for contact_id in items_list:
                if contact_id.isdigit():
                    query = query | Q(user_id=request.user.id, id=contact_id)
                    objects_deleted = True
            if objects_deleted:
                delete_count = OrderItem.objects.filter(query).delete()[0]
            return JsonResponse({'Status': True, 'Удалено объектов': delete_count})
        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})


    # Обновить контакт
    def put(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
             return JsonResponse({'Status': False, 'Error': 'Требуется войти в систему'}, status=403)
         
        if 'id' in Request.data:
            if request['id'].isdigit():
                contact = Contact.objects.filter(id=request.data['id'], user_id=request.user.id).first()
                print(contact)
                if contact:
                    serializer = ContactSerializer(contact, data=request.data, patrial=True)
                    if serializer.is_valid():
                        serializer.save()
                        return JsonResponse({'Status': True})
                    else: 
                        return JsonResponse({'Status': False, "Errors": serializer.errors})
                return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})

            

# Получение и размещение заказов пользователями

class OrderView(APIView):
    
    # Получить мои заказы

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
             return JsonResponse({'Status': False, 'Error': 'Требуется войти в систему'}, status=403)
        

        order = Order.objects.filter(user_id=request.user.id).exclude(state='basket').prefetch_related(
                'ordered_items__product_info__product__category',
                'ordered_items__product_info__product_parameters__parameter').select_related('contact').annotate(
                total_sum = Sum(F('ordered_items__quantity') * F('ordered_items__product_info__price'))).distinct()
        
        serializer = OrderSerializer(order, many=True)
        return JsonResponse(serializer.data)


    # Разместить заказы из корзины

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
             return JsonResponse({'Status': False, 'Error': 'Требуется войти в систему'}, status=403)
        

        if {'id', 'contact'}.issubset(request.data):
            if request.data['id'].isdigit:
                try:
                    is_update = Order.objects.filter(
                        user_id=request.data.id, id=request.data['id'].update(contact_id=request.data['contact'], state='new'))

                except IntegrityError as error:
                    print(error)
                return JsonResponse({'Status': False, 'Errors': 'Не правильно указаны аргументы'})
            else:
                if is_update:
                    new_order.send(sender=self.__class__, user_is=request.user.id)
                    return JsonResponse({'Status': True})
        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})


                
                
                    


