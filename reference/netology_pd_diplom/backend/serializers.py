from rest_framework import serializers


from models import User, Shop, Category, Order, OrderItem, Supplier, Contact, Product, InfoProduct, ProductParametr, ConfirmEmailToken


class ContacSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ('id', 'user', 'city', 'street', 'house', 'appartmet', 'phone',)
        read_only_fields = ('id',)
        extra_kwargs = {'user': {'write_only': True}}


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name',)
        read_only_fields = ('id',)

class UserSerializer(serializers.ModelSerializer):
    contacts = ContacSerializer(read_only = True, many = True)
    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name' 'email', 'company', 'position', 'contacts',)
        read_only_fields = ('id',)


class ShopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = ('id', 'name', 'state',)


class ProducSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = ('name', 'category',)

class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'name', 'email', 'phone',)
        read_only_fields = ('id',)


class ProductParametrSerializer(serializers.ModelSerializer):
    parametr = serializers.StringRelatedField()

    class Meta:
        model = User
        fields = ('model', 'appearence', 'shop', 'phone', 'quantiti', 'price', 'price_rss', 'product_parameters',)
        read_only_fields = ('id',)

class InfoProductSerializer(serializers.ModelSerializer):
    product = ProducSerializer(read_only = True)
    product_parametr = ProductParametrSerializer(read_only = True, many = True)

    class Meta:
        model = User
        fields = ('model', 'appearence', 'shop', 'phone', 'quantiti', 'price', 'price_rss', 'product_parameters',)
        read_only_fields = ('id',)


class OrderItemCreateSerializer():
    product_info = InfoProductSerializer(read_only = True)


class OrderSerializer(serializers.ModelSerializer):
    ordered_items = OrderItemCreateSerializer(read_only = True, many = True)
    total_sum = serializers.IntegerField()
    contact = ConnectionResetError(read_only = True)

    class Meta:
        model = Order
        fields = ('id', 'ordered_items ', 'dtime', 'state', 'total_sum' 'contact',)
        read_only_fields = ('id',)


class ProductParametrSerializer(serializers.ModelSerializer):
    parametr = serializers.StringRelatedField()

    class Meta:
        model = User
        fields = ('model', 'appearence', 'shop', 'phone', 'quantiti', 'price', 'price_rss', 'product_parameters',)
        read_only_fields = ('id',)


class OrderItemSerializer():
    class Meta:
        model = OrderItem
        fields = ('id', 'order', 'info_product', 'quantity',)
        read_only_fields = ('id',)
        extra_kwargs = {'order': {'write_only': True}}




