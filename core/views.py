from django.conf import settings
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import ListView, DetailView, View

from .forms import CheckoutForm
from .models import CheckoutAddress, Order, OrderProduct, Payment, Product
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
import stripe

stripe.api_key = settings.STRIPE_KEY

# Create your views here.
class ProductListView(ListView):
    model = Product
    template_name = "index.html"

class ProductDetailView(DetailView):
    model = Product
    template_name = "detail-product.html"

class OrderSummaryView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            context = {
                'object': order
            }
            return render(self.request, 'order-summary.html', context)
        except ObjectDoesNotExist:
            messages.error(self.request, 'You do not have an order!')
            return redirect('/')
        
class CheckoutView(View):
    def get(self, *args, **kwargs):
        form = CheckoutForm()
        order = Order.objects.get(user=self.request.user, ordered=False)
        context = {
            'form': form,
            'order': order
        }
        return render(self.request, 'checkout.html', context)
    
    def post(self, *args, **kwargs):
        form = CheckoutForm(self.request.POST or None)

        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            if form.is_valid():
                street_address = form.cleaned_data.get('street_address')
                apartment_address = form.cleaned_data.get('apartment_address')
                country = form.cleaned_data.get('country')
                zip = form.cleaned_data.get('zip')
                same_billing_address = form.cleaned_data.get('same_billing_address')
                save_info = form.cleaned_data.get('save_info')
                payment_option = form.cleaned_data.get('payment_option')

                checkout_address = CheckoutAddress(
                    user=self.request.user,
                    street_address=street_address,
                    apartment_address=apartment_address,
                    country=country,
                    zip=zip,
                )
                checkout_address.save()
                order.checkout_address = checkout_address
                order.save()

                if payment_option == 'S':
                    return redirect('core:payment', payment_option='stripe')
                elif payment_option == 'P':
                    return redirect('core:payment', payment_option='paypal')
                else:
                    messages.warning(self.request, 'Invalid payment option')
                    return redirect('core:checkout')
        
        except ObjectDoesNotExist:
            messages.error(self.request, 'You do not have an order!')
            return redirect('core:order-summary')
        
class PaymentView(View):
    def get(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        context = {
            'order': order
        }
        return render(self.request, "payment.html", context)

    def post(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        token = self.request.POST.get('stripeToken')
        amount = int(order.get_total_price() * 100)  #cents

        try:
            charge = stripe.Charge.create(
                amount=amount,
                currency="usd",
                source=token
            )

            # create payment
            payment = Payment()
            payment.stripe_id = charge['id']
            payment.user = self.request.user
            payment.amount = order.get_total_price()
            payment.save()

            # assign payment to order
            order.ordered = True
            order.payment = payment
            order.save()

            messages.success(self.request, "Success make an order")
            return redirect('/')

        except stripe.error.CardError as e:
            body = e.json_body
            err = body.get('error', {})
            messages.error(self.request, f"{err.get('message')}")
            return redirect('/')

        except stripe.error.RateLimitError as e:
            # Too many requests made to the API too quickly
            messages.error(self.request, "To many request error")
            return redirect('/')

        except stripe.error.InvalidRequestError as e:
            # Invalid parameters were supplied to Stripe's API
            messages.error(self.request, "Invalid Parameter")
            return redirect('/')

        except stripe.error.AuthenticationError as e:
            # Authentication with Stripe's API failed
            # (maybe you changed API keys recently)
            messages.error(self.request, "Authentication with stripe failed")
            return redirect('/')

        except stripe.error.APIConnectionError as e:
            # Network communication with Stripe failed
            messages.error(self.request, "Network Error")
            return redirect('/')

        except stripe.error.StripeError as e:
            # Display a very generic error to the user, and maybe send
            # yourself an email
            messages.error(self.request, "Something went wrong")
            return redirect('/')
        
        except Exception as e:
            # Something else happened, completely unrelated to Stripe
            messages.error(self.request, "Not identified error")
            return redirect('/')

@login_required
def add_to_cart(request, pk):
    product = get_object_or_404(Product, pk=pk)
    order_product, created = OrderProduct.objects.get_or_create(
        product=product,
        user=request.user,
        ordered=False
    )
    order_qs=Order.objects.filter(user=request.user, ordered=False)

    if order_qs.exists():
        order=order_qs[0]

        if order.products.filter(product__pk=product.pk).exists():
            order_product.quantity+=1
            order_product.save()
            messages.info(request, 'Added quantity item')
            return redirect('core:order-summary', pk=pk)
        else:
            order.products.add(order_product)
            messages.info(request, 'Product added to your cart')
            return redirect('core:order-summary', pk=pk)
    else:
        ordered_date = timezone.now()
        order=Order.objects.create(user=request.user, ordered_at=ordered_date)
        order.products.add(order_product)
        messages.info(request, 'Item added to your cart')
        return redirect('core:order-summary', pk=pk)
    
@login_required
def remove_from_cart(request, pk):
    product=get_object_or_404(Product, pk=pk)
    order_qs=Order.objects.filter(
        user=request.user,
        ordered=False
    )

    if order_qs.exists():
        order=order_qs[0]
        if order.products.filter(product__pk=product.pk).exists():
            order_product=OrderProduct.objects.filter(
                product=product,
                user=request.user,
                ordered=False
            )[0]
            order_product.delete()
            messages.info(request, 'Product "' + order_product.product.name+'" remove from your cart')
            return redirect('core:index')
        else:
            messages.info(request, 'This product not in your cart')
            return redirect('core:detail-product', pk=pk)
    else:
        messages.info(request, 'You do not have an order')
        return redirect('core:detail-product', pk=pk)

@login_required
def reduce_quantity(request, pk):
    product = get_object_or_404(Product, pk=pk)
    order_qs = Order.objects.filter(
        user = request.user,
        ordered = False
    )
    if order_qs.exists():
        order = order_qs[0]
        if order.products.filter(product__pk=product.pk).exists():
            order_product = OrderProduct.objects.filter(
                product = product,
                user = request.user,
                ordered = False
            )[0]
            if order_product.quantity > 1:
                order_product.quantity -= 1
                order_product.save()
            else:
                order_product.delete()
            messages.info(request, 'Product quantity was updated!')
            return redirect('core:order-summary', pk)
        else:
            messages.info(request, 'This product not in your cart!')
            return redirect('core:order-summary')
    else:
        messages.info(request, 'You do not have an order!')
        return redirect('core:index')
