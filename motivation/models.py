from django.db import models
from django.conf import settings

# Create your models here.

class Product(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='motivation/products/')
    price = models.PositiveIntegerField(help_text='Цена в коинах')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Purchase(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='purchases')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    purchased_at = models.DateTimeField(auto_now_add=True)
    received = models.BooleanField(default=False)  # <-- добавить это поле

    def __str__(self):
        return f'{self.student} купил {self.product}'

class Cart(models.Model):
    student = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cart')
    products = models.ManyToManyField(Product, blank=True)

    def __str__(self):
        return f'Корзина {self.student}'
