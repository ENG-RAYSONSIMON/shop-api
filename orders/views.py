from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Cart, CartItem, Order
from .serializers import (
    AddCartItemSerializer,
    CartSerializer,
    CheckoutSerializer,
    OrderSerializer,
    UpdateCartItemQuantitySerializer,
)


class CartDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        serializer = CartSerializer(cart)
        return Response(serializer.data)


class CartItemAddView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = AddCartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        cart, _ = Cart.objects.get_or_create(user=request.user)
        product = serializer.validated_data["product"]
        quantity = serializer.validated_data["quantity"]

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={"quantity": quantity},
        )

        if not created:
            new_quantity = cart_item.quantity + quantity
            if new_quantity > product.stock:
                return Response(
                    {
                        "quantity": (
                            f"Only {product.stock} item(s) available in stock for {product.name}."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            cart_item.quantity = new_quantity
            cart_item.save(update_fields=["quantity"])
        elif quantity > product.stock:
            cart_item.delete()
            return Response(
                {
                    "quantity": (
                        f"Only {product.stock} item(s) available in stock for {product.name}."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(CartSerializer(cart).data, status=status.HTTP_201_CREATED)


class CartItemUpdateDeleteView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk):
        serializer = UpdateCartItemQuantitySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        cart_item = generics.get_object_or_404(
            CartItem.objects.select_related("cart", "product"),
            pk=pk,
            cart__user=request.user,
        )
        quantity = serializer.validated_data["quantity"]

        if quantity > cart_item.product.stock:
            return Response(
                {
                    "quantity": (
                        f"Only {cart_item.product.stock} item(s) available in stock "
                        f"for {cart_item.product.name}."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        cart_item.quantity = quantity
        cart_item.save(update_fields=["quantity"])
        return Response(CartSerializer(cart_item.cart).data)

    def delete(self, request, pk):
        cart_item = generics.get_object_or_404(
            CartItem.objects.select_related("cart"),
            pk=pk,
            cart__user=request.user,
        )
        cart = cart_item.cart
        cart_item.delete()
        return Response(CartSerializer(cart).data, status=status.HTTP_200_OK)


class CheckoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = CheckoutSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


class OrderListView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return Order.objects.prefetch_related("items__product").all().order_by("-ordered_at")
        return (
            Order.objects.prefetch_related("items__product")
            .filter(user=user)
            .order_by("-ordered_at")
        )


class OrderDetailView(generics.RetrieveAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return Order.objects.prefetch_related("items__product").all()
        return Order.objects.prefetch_related("items__product").filter(user=user)
