from django.urls import path

from . import views

app_name = 'core'

urlpatterns = [
  path('', views.ProductListView.as_view(), name='index'),
  path('product/<pk>', views.ProductDetailView.as_view(), name='detail-product'),
  path('order-summary/<pk>', views.OrderSummaryView.as_view(), name='order-summary'),
  path('checkout', views.CheckoutView.as_view(), name='checkout'),
  path('payment/<payment_option>', views.PaymentView.as_view(), name='payment'),
  path('add-to-cart/<pk>', views.add_to_cart, name='add-to-cart'),
  path('remove-from-cart/<pk>', views.remove_from_cart, name='remove-from-cart'),
  path('reduce-quantity/<pk>', views.reduce_quantity, name='reduce-quantity'),
]