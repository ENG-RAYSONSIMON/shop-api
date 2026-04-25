from decimal import Decimal

from django.db import transaction
from rest_framework import serializers

from products.models import Product

from .models import Cart, CartItem, Order, OrderItem


class CartItemSerializer(serializers.ModelSerializer):
    product_name = serializers.ReadOnlyField(source="product.name")
    unit_price = serializers.ReadOnlyField(source="product.price")
    line_total = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ["id", "product", "product_name", "unit_price", "quantity", "line_total"]

    def get_line_total(self, obj):
        return obj.product.price * obj.quantity


class CartSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source="user.username")
    items = CartItemSerializer(many=True, read_only=True)
    total = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ["id", "user", "items", "total", "created_at", "updated_at"]

    def get_total(self, obj):
        total = Decimal("0.00")
        for item in obj.items.select_related("product"):
            total += item.product.price * item.quantity
        return total


class AddCartItemSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    quantity = serializers.IntegerField(min_value=1)


class UpdateCartItemQuantitySerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1)


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.ReadOnlyField(source="product.name")

    class Meta:
        model = OrderItem
        fields = ["id", "product", "product_name", "price_at_purchase", "quantity", "line_total"]


class OrderSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source="user.username")
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ["id", "user", "status", "total_price", "ordered_at", "updated_at", "items"]


class CheckoutSerializer(serializers.Serializer):
    def save(self, **kwargs):
        user = self.context["request"].user

        with transaction.atomic():
            cart, _ = Cart.objects.get_or_create(user=user)
            cart_items = list(cart.items.select_related("product").order_by("product_id"))

            if not cart_items:
                raise serializers.ValidationError({"cart": "Cannot checkout an empty cart."})

            product_ids = [item.product_id for item in cart_items]
            locked_products = {
                product.id: product
                for product in Product.objects.select_for_update().filter(id__in=product_ids)
            }

            order = Order.objects.create(user=user)
            total = Decimal("0.00")

            for cart_item in cart_items:
                product = locked_products[cart_item.product_id]

                if product.stock == 0:
                    raise serializers.ValidationError(
                        {"product": f"{product.name} is out of stock."}
                    )

                if cart_item.quantity > product.stock:
                    raise serializers.ValidationError(
                        {
                            "quantity": (
                                f"Requested {cart_item.quantity} of {product.name}, "
                                f"but only {product.stock} available."
                            )
                        }
                    )

                order_item = OrderItem.objects.create(
                    order=order,
                    product=product,
                    price_at_purchase=product.price,
                    quantity=cart_item.quantity,
                )
                total += order_item.line_total

                product.stock -= cart_item.quantity
                product.save(update_fields=["stock"])

            order.total_price = total
            order.save(update_fields=["total_price", "updated_at"])

            cart.items.all().delete()

        return order
