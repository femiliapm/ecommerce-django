from django.contrib import admin
from .models import Order, OrderProduct, Payment, Product 

# Register your models here.
class ProductAdmin(admin.ModelAdmin):
  list_display = ('id', 'name', 'price')

class OrderAdmin(admin.ModelAdmin):
  list_display = ('id', 'user')

admin.site.register(Product, ProductAdmin)
admin.site.register(OrderProduct)
admin.site.register(Order, OrderAdmin)
admin.site.register(Payment)
