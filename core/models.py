import uuid
from django.conf import settings
from django.db import models
from django.shortcuts import reverse
from django_countries.fields import CountryField

# Create your models here.
CATEGORY = (
  ('S', 'Shirt'),
  ('SW', 'Sport Wear'),
  ('OW', 'Out Wear'),
)

LABEL = (
  ('N', 'New'),
  ('BS', 'Best Seller'),
  ('E', 'Eco'),
)

class Product(models.Model):
  """Model definition for Product."""

  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  name = models.CharField(max_length=100)
  image_url = models.CharField(max_length=255, null=True)
  price = models.FloatField()
  discount = models.FloatField(blank=True, null=True)
  category = models.CharField(choices=CATEGORY, max_length=2)
  label = models.CharField(choices=LABEL, max_length=2)
  description = models.TextField()

  class Meta:
    """Meta definition for Product."""

    verbose_name = 'Product'
    verbose_name_plural = 'Products'

  def __str__(self):
    """Unicode representation of Product."""
    return self.name
  
  def get_absolute_url(self):
    return reverse('core:detail-product', kwargs={'pk': self.pk})
  
  def get_add_to_cart_url(self):
    return reverse('core:add-to-cart', kwargs={
      'pk': self.pk
    })
  
  def get_remove_from_cart_url(self):
    return reverse('core:remove-from-cart', kwargs={
      'pk': self.pk
    })
  
class OrderProduct(models.Model):
  """Model definition for OrderProduct."""

  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
  ordered = models.BooleanField(default=False)
  product = models.ForeignKey(Product, on_delete=models.CASCADE)
  quantity = models.IntegerField(default=1)

  class Meta:
    """Meta definition for OrderProduct."""

    verbose_name = 'OrderProduct'
    verbose_name_plural = 'OrderProducts'

  def __str__(self):
    """Unicode representation of OrderProduct."""
    return f'{self.quantity} of {self.product.name}'
  
  def get_total_product_price(self):
    return self.quantity * self.product.price
  
  def get_discount_product_price(self):
    return self.quantity * self.product.discount
  
  def get_amount_saved(self):
    return self.get_total_product_price() - self.get_discount_product_price()
  
  def get_final_price(self):
    if self.product.discount:
      return self.get_discount_product_price()
    return self.get_total_product_price()
  
class Order(models.Model):
  """Model definition for Order."""

  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
  products = models.ManyToManyField(OrderProduct)
  start_date = models.DateTimeField(auto_now_add=True)
  ordered_at = models.DateTimeField()
  ordered = models.BooleanField(default=False)

  class Meta:
    """Meta definition for Order."""

    verbose_name = 'Order'
    verbose_name_plural = 'Orders'

  def __str__(self):
    """Unicode representation of Order."""
    return self.user.username
  
  def get_total_price(self):
    total = 0
    for order_product in self.products.all():
      total += order_product.get_final_price()
    return total

class CheckoutAddress(models.Model):
  """Model definition for CheckoutAddress."""

  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
  street_address = models.CharField(max_length=100)
  apartment_address = models.CharField(max_length=100)
  country = CountryField(multiple=False)
  zip = models.CharField(max_length=100)

  class Meta:
    """Meta definition for CheckoutAddress."""

    verbose_name = 'CheckoutAddress'
    verbose_name_plural = 'CheckoutAddresses'

  def __str__(self):
    """Unicode representation of CheckoutAddress."""
    return self.user.username

class Payment(models.Model):
  """Model definition for Payment."""

  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  stripe_id = models.CharField(max_length=50)
  user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True)
  amount = models.FloatField()
  timestamp = models.DateTimeField(auto_now_add=True)

  class Meta:
    """Meta definition for Payment."""

    verbose_name = 'Payment'
    verbose_name_plural = 'Payments'

  def __str__(self):
    """Unicode representation of Payment."""
    return self.user.username

