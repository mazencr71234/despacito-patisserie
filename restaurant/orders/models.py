from django.db import models
from django.contrib.auth.hashers import make_password, check_password

class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class MenuItem(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='items')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    image = models.ImageField(upload_to='menu_images/', blank=True, null=True)
    available = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Order(models.Model):
    customer_name = models.CharField(max_length=100, verbose_name="الاسم الثلاثي")
    table_number = models.PositiveIntegerField(verbose_name="رقم الطاولة")
    phone = models.CharField(max_length=20, verbose_name="رقم الهاتف")
    confirmation_code = models.CharField(
        max_length=20, blank=True, null=True, verbose_name="رقم تأكيد الطلب (يحدده الأدمن)"
    )
    total_price = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    STATUS_CHOICES = [
        ('pending', 'قيد الانتظار'),
        ('confirmed', 'تم التأكيد'),
        ('delivered', 'تم التسليم'),
        ('cancelled', 'ملغي'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"طلب #{self.id} - {self.customer_name}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    item_price = models.DecimalField(max_digits=6, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.menu_item.name}"

class SiteSetting(models.Model):
    confirmation_code = models.CharField(max_length=255, default='mazen123', verbose_name="رقم تأكيد الطلب")

    def save(self, *args, **kwargs):
        if not self.pk and SiteSetting.objects.exists():
            raise Exception("يوجد بالفعل إعدادات للموقع، يمكنك تعديلها فقط.")
        # Hash the confirmation code before saving
        if self.confirmation_code and not self.confirmation_code.startswith('pbkdf2_sha256$'):
            self.confirmation_code = make_password(self.confirmation_code)
        super().save(*args, **kwargs)

    def __str__(self):
        return "إعدادات الموقع"

    class Meta:
        verbose_name = "إعدادات الموقع"
        verbose_name_plural = "إعدادات الموقع"