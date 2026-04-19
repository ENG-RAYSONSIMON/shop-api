from django.db import transaction
from rest_framework import serializers

from products.models import Product

from .models import Order


class OrderSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')
    total_price = serializers.ReadOnlyField()
    status = serializers.ReadOnlyField()

    class Meta:
        model = Order
        fields = ['id', 'user', 'product', 'quantity', 'status', 'total_price', 'ordered_at']

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError('Quantity must be greater than 0.')
        return value

    def validate(self, attrs):
        product = attrs.get('product')
        quantity = attrs.get('quantity', 0)

        if product.stock == 0:
            raise serializers.ValidationError({'product': 'This product is out of stock.'})

        if quantity > product.stock:
            raise serializers.ValidationError(
                {'quantity': f'Only {product.stock} item(s) available in stock.'}
            )

        return attrs

    def create(self, validated_data):
        with transaction.atomic():
            product = Product.objects.select_for_update().get(pk=validated_data['product'].pk)
            quantity = validated_data['quantity']

            if product.stock == 0:
                raise serializers.ValidationError({'product': 'This product is out of stock.'})

            if quantity > product.stock:
                raise serializers.ValidationError(
                    {'quantity': f'Only {product.stock} item(s) available in stock.'}
                )

            product.stock -= quantity
            product.save(update_fields=['stock'])

            order = Order.objects.create(**validated_data)

        return order
