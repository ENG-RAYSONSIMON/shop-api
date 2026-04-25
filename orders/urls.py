from django.urls import path

from .views import (
    CartDetailView,
    CartItemAddView,
    CartItemUpdateDeleteView,
    CheckoutView,
    OrderDetailView,
    OrderListView,
)

urlpatterns = [
    path("cart/", CartDetailView.as_view(), name="cart-detail"),
    path("cart/items/", CartItemAddView.as_view(), name="cart-item-add"),
    path("cart/items/<int:pk>/", CartItemUpdateDeleteView.as_view(), name="cart-item-update-delete"),
    path("checkout/", CheckoutView.as_view(), name="checkout"),
    path("", OrderListView.as_view(), name="order-list-create"),
    path("<int:pk>/", OrderDetailView.as_view(), name="order-detail"),
]
