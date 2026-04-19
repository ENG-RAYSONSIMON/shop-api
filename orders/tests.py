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

    def test_authenticated_user_can_create_order_and_total_is_computed(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            reverse("order-list-create"),
            {"product": self.product.id, "quantity": 3},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(str(response.data["total_price"]), "150.00")

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
