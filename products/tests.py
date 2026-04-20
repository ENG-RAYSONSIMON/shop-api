from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from products.models import Product
from users.models import User


class ProductAPITests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="owner",
            email="owner@example.com",
            password="StrongPass123",
        )
        self.other_user = User.objects.create_user(
            username="other",
            email="other@example.com",
            password="StrongPass123",
        )
        self.product = Product.objects.create(
            user=self.owner,
            name="Keyboard",
            description="Mechanical keyboard",
            price="89.99",
            stock=10,
        )

    def test_anyone_can_list_products(self):
        response = self.client.get(reverse("product-list-create"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_anyone_can_retrieve_product(self):
        response = self.client.get(reverse("product-detail", args=[self.product.id]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.product.id)

    def test_authenticated_user_can_create_product(self):
        self.client.force_authenticate(user=self.owner)

        response = self.client.post(
            reverse("product-list-create"),
            {
                "name": "Mouse",
                "description": "Wireless mouse",
                "price": "24.99",
                "stock": 5,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Product.objects.count(), 2)
        self.assertEqual(Product.objects.latest("id").user, self.owner)

    def test_unauthenticated_user_cannot_create_product(self):
        response = self.client.post(
            reverse("product-list-create"),
            {
                "name": "Mouse",
                "description": "Wireless mouse",
                "price": "24.99",
                "stock": 5,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_non_owner_cannot_update_another_users_product(self):
        self.client.force_authenticate(user=self.other_user)

        response = self.client.patch(
            reverse("product-detail", args=[self.product.id]),
            {"price": "79.99"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_owner_can_update_their_own_product(self):
        self.client.force_authenticate(user=self.owner)

        response = self.client.patch(
            reverse("product-detail", args=[self.product.id]),
            {"price": "79.99"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertEqual(str(self.product.price), "79.99")
