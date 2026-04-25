from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from orders.models import Cart, CartItem, Order
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
        self.admin_user = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="StrongPass123",
            is_staff=True,
        )
        self.product = Product.objects.create(
            user=self.other_user,
            name="Headphones",
            description="Noise cancelling",
            price="50.00",
            stock=8,
        )
        self.second_product = Product.objects.create(
            user=self.other_user,
            name="Mouse",
            description="Wireless mouse",
            price="25.00",
            stock=3,
        )

    def test_authenticated_user_can_view_cart(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(reverse("cart-detail"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["user"], self.user.username)
        self.assertEqual(response.data["items"], [])

    def test_authenticated_user_can_add_item_to_cart(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            reverse("cart-item-add"),
            {"product": self.product.id, "quantity": 2},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data["items"]), 1)
        self.assertEqual(response.data["items"][0]["quantity"], 2)

    def test_add_item_increments_existing_cart_item_quantity(self):
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product, quantity=2)
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            reverse("cart-item-add"),
            {"product": self.product.id, "quantity": 3},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        cart_item = CartItem.objects.get(cart=cart, product=self.product)
        self.assertEqual(cart_item.quantity, 5)

    def test_user_can_update_cart_item_quantity(self):
        cart = Cart.objects.create(user=self.user)
        cart_item = CartItem.objects.create(cart=cart, product=self.product, quantity=1)
        self.client.force_authenticate(user=self.user)

        response = self.client.patch(
            reverse("cart-item-update-delete", args=[cart_item.id]),
            {"quantity": 4},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        cart_item.refresh_from_db()
        self.assertEqual(cart_item.quantity, 4)

    def test_user_can_remove_cart_item(self):
        cart = Cart.objects.create(user=self.user)
        cart_item = CartItem.objects.create(cart=cart, product=self.product, quantity=1)
        self.client.force_authenticate(user=self.user)

        response = self.client.delete(reverse("cart-item-update-delete", args=[cart_item.id]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(CartItem.objects.filter(id=cart_item.id).exists())

    def test_checkout_creates_order_with_multiple_order_items(self):
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product, quantity=2)
        CartItem.objects.create(cart=cart, product=self.second_product, quantity=3)
        self.client.force_authenticate(user=self.user)

        response = self.client.post(reverse("checkout"), {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], Order.STATUS_PENDING)
        self.assertEqual(str(response.data["total_price"]), "175.00")
        self.assertEqual(len(response.data["items"]), 2)

        self.product.refresh_from_db()
        self.second_product.refresh_from_db()
        self.assertEqual(self.product.stock, 6)
        self.assertEqual(self.second_product.stock, 0)
        self.assertEqual(CartItem.objects.filter(cart=cart).count(), 0)

    def test_reject_checkout_when_cart_is_empty(self):
        Cart.objects.create(user=self.user)
        self.client.force_authenticate(user=self.user)

        response = self.client.post(reverse("checkout"), {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("cart", response.data)

    def test_reject_checkout_when_item_quantity_exceeds_stock(self):
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.second_product, quantity=5)
        self.client.force_authenticate(user=self.user)

        response = self.client.post(reverse("checkout"), {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("quantity", response.data)

    def test_normal_user_only_sees_their_own_orders(self):
        user_cart = Cart.objects.create(user=self.user)
        other_cart = Cart.objects.create(user=self.other_user)
        CartItem.objects.create(cart=user_cart, product=self.product, quantity=1)
        CartItem.objects.create(cart=other_cart, product=self.product, quantity=1)

        self.client.force_authenticate(user=self.user)
        self.client.post(reverse("checkout"), {}, format="json")

        self.client.force_authenticate(user=self.other_user)
        self.client.post(reverse("checkout"), {}, format="json")

        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse("order-list-create"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["user"], self.user.username)

    def test_admin_can_list_all_orders(self):
        user_cart = Cart.objects.create(user=self.user)
        other_cart = Cart.objects.create(user=self.other_user)
        CartItem.objects.create(cart=user_cart, product=self.product, quantity=1)
        CartItem.objects.create(cart=other_cart, product=self.product, quantity=1)

        self.client.force_authenticate(user=self.user)
        self.client.post(reverse("checkout"), {}, format="json")

        self.client.force_authenticate(user=self.other_user)
        self.client.post(reverse("checkout"), {}, format="json")

        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(reverse("order-list-create"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 2)

    def test_normal_user_cannot_retrieve_another_users_order(self):
        other_cart = Cart.objects.create(user=self.other_user)
        CartItem.objects.create(cart=other_cart, product=self.product, quantity=1)

        self.client.force_authenticate(user=self.other_user)
        checkout_response = self.client.post(reverse("checkout"), {}, format="json")
        other_order_id = checkout_response.data["id"]

        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse("order-detail", args=[other_order_id]))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
