from rest_framework import serializers
from .models import MenuItem, Category, Cart,Order, OrderItem
from django.contrib.auth.models import User
from rest_framework.exceptions import ValidationError


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id','slug','title']


class MenuItemSerializer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(slug_field='title', queryset=Category.objects.all())

    class Meta:
        model = MenuItem
        fields = ['id', 'title', 'price', 'featured', 'category']

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be a positive number.")
        return value

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']

class CartSerializer(serializers.ModelSerializer):
    menuitem = serializers.CharField()  # Use CharField for menuitem

    class Meta:
        model = Cart
        fields = ['user', 'menuitem', 'quantity', 'unit_price', 'total_price']
        read_only_fields = ['user', 'unit_price', 'total_price']

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be a positive number.")
        return value

    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user if request and request.user.is_authenticated else None

        menuitem_title = validated_data.pop('menuitem')  # Extract menuitem_name
        quantity = validated_data.get('quantity')

        if not user:
            raise ValidationError("User must be authenticated to add items to the cart.")

        # Try to get the MenuItem object by name
        try:
            menuitem = MenuItem.objects.get(title=menuitem_title)
        except MenuItem.DoesNotExist:
            raise ValidationError(f"Menu item with name '{menuitem_title}' does not exist.")

        # Calculate unit_price based on menuitem's price
        unit_price = menuitem.price

        # Calculate total_price based on quantity and unit_price
        total_price = quantity * unit_price

        # Create the cart item
        cart_item = Cart.objects.create(
            user=user,
            menuitem=menuitem,
            unit_price=unit_price,
            total_price=total_price,
            **validated_data  # This includes 'quantity'
        )

        return cart_item
    
    
    
    
    
class OrderItemSerializer(serializers.ModelSerializer):
    menuitem = serializers.StringRelatedField()

    class Meta:
        model = OrderItem
        fields = ['menuitem', 'quantity', 'unit_price', 'price']

class OrderSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source='user.username')
    order_items = OrderItemSerializer(many=True, read_only=True)
    delivery_crew = serializers.StringRelatedField()

    class Meta:
        model = Order
        fields = ['id', 'user', 'total', 'delivery_crew','status','date', 'order_items']
        read_only_fields = ['user', 'total', 'date', 'order_items']

    def create(self, validated_data):
        order_items_data = validated_data.pop('order_items', [])
        order = Order.objects.create(**validated_data)

        for order_item_data in order_items_data:
            menuitem_str = order_item_data.pop('menuitem')  
            menuitem = MenuItem.objects.get(title=menuitem_str) 

            OrderItem.objects.create(order=order, menuitem=menuitem, **order_item_data)

        return order





        