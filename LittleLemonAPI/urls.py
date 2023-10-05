from django.urls import path,include
from . import views
from rest_framework.authtoken.views import obtain_auth_token


urlpatterns = [
    path('menu-items', views.MenuView.as_view({'get': 'list', 'post': 'create', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'})),
    path('menu-items/<int:pk>',views.MenuView.as_view({'get': 'retrieve', 'post': 'create', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'})),
    path('groups/manager/users',views.manager),
    path('groups/manager/users/<int:userId>',views.manager),
    path('groups/delivery-crew/users',views.delivery),
    path('groups/delivery-crew/users/<int:userId>',views.delivery),
    path('cart/menu-items',views.add_to_cart),
    path('orders',views.create_order),
    path('orders/<int:orderId>',views.create_order),
    path('order-items', views.order_items_view),
    path('token/login/', obtain_auth_token),  
    path('__debug__/', include('debug_toolbar.urls')),
]