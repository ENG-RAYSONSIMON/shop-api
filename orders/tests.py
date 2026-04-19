from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from orders.models import Order
from products.models import Product
from users.models import User


class OrderAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="buyer",
            email="buyer@example.com",
            password="StrongPass123",
        )
        self.other_user = User.objects.create_user(
            username="someoneelse",
            email="someoneelse@example.com",
            password="StrongPass123",
        )
        self.product = Product.objects.create(
            user=self.other_user,
            name="Headphones",
            description="Noise cancelling",
            price="50.00",
            stock=8,
        )
        self.order = Order.objects.create(
            user=self.user,
            product=self.product,
            quantity=2,
        )

    def test_successful_order_creation(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            reverse("order-list-create"),
            {"product": self.product.id, "quantity": 3},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], Order.STATUS_PENDING)

    def test_total_price_calculation(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            reverse("order-list-create"),
            {"product": self.product.id, "quantity": 3},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(str(response.data["total_price"]), "150.00")

    def test_stock_reduction_after_order(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            reverse("order-list-create"),
            {"product": self.product.id, "quantity": 3},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 5)

    def test_reject_order_when_stock_is_zero(self):
        self.client.force_authenticate(user=self.user)
        self.product.stock = 0
        self.product.save(update_fields=['stock'])

        response = self.client.post(
            reverse("order-list-create"),
            {"product": self.product.id, "quantity": 1},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("product", response.data)

    def test_reject_order_when_quantity_exceeds_stock(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            reverse("order-list-create"),
            {"product": self.product.id, "quantity": 99},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("quantity", response.data)

    def test_reject_order_when_quantity_is_zero_or_less(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            reverse("order-list-create"),
            {"product": self.product.id, "quantity": 0},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("quantity", response.data)

    def test_user_only_sees_their_own_orders(self):
        Order.objects.create(user=self.other_user, product=self.product, quantity=1)
        self.client.force_authenticate(user=self.user)

        response = self.client.get(reverse("order-list-create"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.order.id)

    def test_user_cannot_view_someone_elses_order(self):
        other_order = Order.objects.create(
            user=self.other_user,
            product=self.product,
            quantity=1,
        )
        self.client.force_authenticate(user=self.user)

        response = self.client.get(reverse("order-detail", args=[other_order.id]))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
