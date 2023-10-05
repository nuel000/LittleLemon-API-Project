from django.http import JsonResponse
from django.contrib.auth.models import Group
from django.forms.models import model_to_dict
from django.db.utils import IntegrityError
from .models import MenuItem, Category,Cart,Order,OrderItem
from django.views.decorators.csrf import csrf_exempt
from django.forms.models import model_to_dict
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from .serializers import MenuItemSerializer,CategorySerializer,UserSerializer,CartSerializer, OrderItemSerializer,OrderSerializer
from rest_framework import generics, filters
from django.shortcuts import get_object_or_404
from django_filters import rest_framework as django_filters
from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework.decorators import permission_classes,throttle_classes
from rest_framework.throttling import AnonRateThrottle,UserRateThrottle
from .throttles import TenCallsPerMinute
from rest_framework import viewsets
import django_filters
from rest_framework.permissions import IsAdminUser
from django.contrib.auth.models import User,Group
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
from django_filters.rest_framework import DjangoFilterBackend
customer_group, created = Group.objects.get_or_create(name='Customer')


# Creating permissions for only managers to post, put, delete and patch.
class ManagerPermission(BasePermission):
    def has_permission(self, request, view):
        if request.user and request.user.is_authenticated:
            if request.user.groups.filter(name='Manager').exists():
                return True  # Allow all access for managers
            elif request.method in ('GET', 'HEAD', 'OPTIONS'):
                return True  # Allow read-only access for other users
        return False

# ALL MENU ITEMS 
class MenuView(viewsets.ModelViewSet):
    serializer_class = MenuItemSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    search_fields = ['title']
    ordering_fields = ['price']
    filterset_fields = ['category__title']
    permission_classes = [IsAuthenticated, ManagerPermission]  # Apply custom permission class

    def get_queryset(self):
        queryset = MenuItem.objects.all()
        category_name = self.request.query_params.get('category')
        if category_name:
            queryset = queryset.filter(category__title=category_name)
        ordering = self.request.query_params.get('ordering')
        if ordering:
            queryset = queryset.order_by(ordering)
        return queryset
    
 # Managers View
@api_view(['GET', 'POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def manager(request, userId=None):  # Make userId optional with a default value of None
    if not request.user.groups.filter(name='Manager').exists():
        return Response({'message': 'You are not authorized to see this message'}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'GET':
        # Retrieve all managers
        managers = User.objects.filter(groups__name='Manager')
        # Serialize the managers
        serializer = UserSerializer(managers, many=True)
        return Response({'managers': serializer.data})

    elif request.method == 'POST':
        username = request.data.get('username')
        if username is None:
            return Response({'message': 'Username is required'}, status=status.HTTP_400_BAD_REQUEST)

        user = get_object_or_404(User, username=username)
        managers_group = Group.objects.get(name="Manager")

        if managers_group.user_set.filter(id=user.id).exists():
            return Response({'message': f'User with username {username} is already a manager'}, status=status.HTTP_400_BAD_REQUEST)

        managers_group.user_set.add(user)
        return Response({'message': f'User with username {username} added to managers'}, status=status.HTTP_201_CREATED)

    elif request.method == 'DELETE':
        if userId is None:
            return Response({'message': 'User ID is required for deletion'}, status=status.HTTP_400_BAD_REQUEST)

        user = get_object_or_404(User, id=userId)
        managers_group = Group.objects.get(name="Manager")

        if not managers_group.user_set.filter(id=user.id).exists():
            return Response({'message': f'User with ID {userId} is not a manager'}, status=status.HTTP_404_NOT_FOUND)

        managers_group.user_set.remove(user)
        return Response({'message': f'User with ID {userId} removed from managers'}, status=status.HTTP_200_OK)

    return Response({'message': 'Invalid request method'}, status=status.HTTP_400_BAD_REQUEST)


# Delivery View
@api_view(['GET', 'POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def delivery(request, userId=None):  # Make userId optional with a default value of None
    if not request.user.groups.filter(name='Manager').exists():
        return Response({'message': 'You are not authorized to see this message'}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'GET':
        # Retrieve all members of the delivery crew
        delivery_crew = User.objects.filter(groups__name='Delivery crew')
        # Serialize the delivery crew
        serializer = UserSerializer(delivery_crew, many=True)
        return Response({'Delivery Crew': serializer.data})

    elif request.method == 'POST':
        username = request.data.get('username')

        if username is None:
            return Response({'message': 'Username is required'}, status=status.HTTP_400_BAD_REQUEST)

        user = get_object_or_404(User, username=username)
        delivery_group = Group.objects.get(name="Delivery crew")

        if delivery_group.user_set.filter(id=user.id).exists():
            return Response({'message': f'User with username {username} is already a member of delivery crew'}, status=status.HTTP_400_BAD_REQUEST)

        delivery_group.user_set.add(user)
        return Response({'message': f'User with username {username} added to delivery crew'}, status=status.HTTP_201_CREATED)

    elif request.method == 'DELETE':
        if userId is None:
            return Response({'message': 'User ID is required for deletion'}, status=status.HTTP_400_BAD_REQUEST)

        user = get_object_or_404(User, id=userId)
        delivery_group = Group.objects.get(name="Delivery crew")

        if not delivery_group.user_set.filter(id=user.id).exists():
            return Response({'message': f'User with ID {userId} is not a delivery crew member'}, status=status.HTTP_404_NOT_FOUND)

        delivery_group.user_set.remove(user)
        return Response({'message': f'User with ID {userId} removed from delivery crew'}, status=status.HTTP_200_OK)

    return Response({'message': 'Invalid request method'}, status=status.HTTP_400_BAD_REQUEST)

# Cart View
@api_view(['GET', 'POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def add_to_cart(request, cart_item_id=None):
    user = request.user
    if request.method == 'GET':
        # Retrieve current items in the cart for the current user
        cart_items = Cart.objects.filter(user=user)
        serializer = CartSerializer(cart_items, many=True)
        if len(serializer.data)==0:
            return Response("Your Cart is Empty")
        return Response({'Here are your cart items':serializer.data})

    elif request.method == 'POST':
        serializer = CartSerializer(data=request.data, context={'request': request})

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        # Delete all items in the cart for the current user
        Cart.objects.filter(user=user).delete()
        return Response({'message': 'All cart items deleted successfully'}, status=status.HTTP_200_OK)
    
# Orders

@api_view(['GET', 'POST', 'PATCH', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def create_order(request, orderId=None):
    user = request.user
    is_manager = user.groups.filter(name='Manager').exists()
    is_delivery_crew = user.groups.filter(name='Delivery crew').exists()
    is_customer = not is_manager and not is_delivery_crew

    # Check if the user is a manager
    is_manager = user.groups.filter(name='Manager').exists()

    if is_manager:
        if request.method == 'GET' and orderId is not None:
            # Manager can see a specific order by ID
            order = get_object_or_404(Order, id=orderId)
            serializer = OrderSerializer(order)
            return Response(serializer.data, status=status.HTTP_200_OK)

        # Manager can see all orders
        elif request.method == 'GET':
            orders = Order.objects.all()
            serializer = OrderSerializer(orders, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        # Manager can delete orders
        elif request.method == 'DELETE' and orderId is not None:
            order = get_object_or_404(Order, id=orderId)
            order.delete()
            return Response({'message': 'Order deleted successfully'}, status=status.HTTP_200_OK)

        # Manager can update orders
        elif request.method in ['PUT', 'PATCH']:
            order = get_object_or_404(Order, id=orderId)
            serializer = OrderSerializer(order, data=request.data, partial=True)

            if serializer.is_valid():
                serializer.save()

                # If the delivery_crew field is provided, check if the assigned user is in the Delivery Crew group
                delivery_crew_username = request.data.get('delivery_crew', None)

                if delivery_crew_username:
                    try:
                        delivery_crew_user = User.objects.get(username=delivery_crew_username)
                        is_delivery_crew = delivery_crew_user.groups.filter(name='Delivery crew').exists()

                        if is_delivery_crew:
                            order.delivery_crew = delivery_crew_user
                            order.save()
                        else:
                            return Response({'message': 'Assigned user is not a member of the Delivery Crew group.'}, status=status.HTTP_400_BAD_REQUEST)
                    except User.DoesNotExist:
                        return Response({'message': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    if is_customer:
        if request.method == 'GET':
            # Retrieve orders created by the current user
            orders = Order.objects.filter(user=user)
            serializer = OrderSerializer(orders, many=True)
            if serializer.data:
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response({'message': 'You have no orders'}, status=status.HTTP_200_OK)

        elif request.method == 'POST':
            cart_items = Cart.objects.filter(user=user)

            # If the cart is empty, return a response indicating that
            if not cart_items.exists():
                return Response({'message': 'Cart is empty. No order created.'}, status=status.HTTP_400_BAD_REQUEST)

            # Calculate the total cost of the order
            total_cost = sum(cart_item.total_price for cart_item in cart_items)

            # Create a new order
            order = Order.objects.create(user=user, total=total_cost)

            # Create order items based on cart items
            for cart_item in cart_items:
                order_item = OrderItem.objects.create(
                    order=order,
                    menuitem=cart_item.menuitem,
                    quantity=cart_item.quantity,
                    unit_price=cart_item.unit_price,
                    price=cart_item.total_price
                )

            # Delete all items in the cart for the current user
            cart_items.delete()

            # Serialize and return the created order
            serializer = OrderSerializer(order)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

    # Check if the user is in the Delivery Crew group
    is_delivery_crew = user.groups.filter(name='Delivery crew').exists()

    if is_delivery_crew:
        if request.method == 'GET' and orderId is not None:
            
            # Retrieve orders assigned to the delivery crew member
            orders = Order.objects.filter(delivery_crew=user,id=orderId)
            if len(orders)==0:
                return Response(f"You are not assigned an Order with id {orderId}")      
            serializer = OrderSerializer(orders, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        elif request.method == 'PATCH':
            if not is_delivery_crew:
                return Response({'message': 'You do not have permission to manage orders.'}, status=status.HTTP_403_FORBIDDEN)
            # Retrieve the order
            order = get_object_or_404(Order, id=orderId)

            # Check if the delivery crew member is assigned to this order
            if order.delivery_crew != user:
                return Response({'message': 'You are not assigned to this order.'}, status=status.HTTP_403_FORBIDDEN)

            # Validate and update the order status
            serializer = OrderSerializer(order, data=request.data, partial=True)

            if serializer.is_valid():
                # Only update the status field
                order.status = request.data.get('status', order.status)
                order.save()

                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    return Response({'message': 'Invalid request method.'}, status=status.HTTP_400_BAD_REQUEST)
    


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def order_items_view(request):
    user = request.user
    order_items = OrderItem.objects.filter(order__user=user)

    serializer = OrderItemSerializer(order_items, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)






