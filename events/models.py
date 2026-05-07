from django.contrib.auth.models import User
from django.db import models

class Event(models.Model):
    name = models.CharField(max_length=100)
    date = models.DateField()
    location = models.CharField(max_length=200)

class Profile(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('owner', 'Owner'),
        ('customer', 'Customer'),
        ('employee', 'Employee (Future Implementation)'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    
    # OTP fields for password reset
    otp = models.CharField(max_length=6, blank=True, null=True)
    otp_created_at = models.DateTimeField(blank=True, null=True)

class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=10)

class Owner(models.Model):
    SERVICE_CHOICES = [
        ('sound', 'Sound'),
        ('light', 'Light'),
        ('led', 'LED Wall'),
        ('sfx', 'Special Effects'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=10)
    company_name = models.CharField(max_length=200)
    business_type = models.CharField(max_length=100)
    location = models.CharField(max_length=200)
    state = models.CharField(max_length=100, blank=True, null=True)
    district = models.CharField(max_length=100)
    license_id = models.CharField(max_length=100)


class Inventory(models.Model):
    CATEGORY_CHOICES = [
        ('sound', 'Sound'),
        ('light', 'Light'),
        ('led', 'LED Wall'),
        ('sfx', 'Special Effects'),
    ]

    owner = models.ForeignKey('Owner', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    subcategory = models.CharField(max_length=100, blank=True, null=True)
    sub_type = models.CharField(max_length=100, blank=True, null=True)
    quantity = models.IntegerField()
    price_per_day = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    images = models.ImageField(upload_to='inventory_images/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=[('Available', 'Available'), ('Out of stock', 'Out of stock')], default='Available')

    def __str__(self):
        return self.name

class Booking(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Completed', 'Completed'),
    ]

    customer = models.ForeignKey(User, on_delete=models.CASCADE)
    item = models.ForeignKey(Inventory, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    start_date = models.DateField()
    end_date = models.DateField()
    district = models.CharField(max_length=100, blank=True, null=True)
    venue = models.CharField(max_length=255, blank=True, null=True)
    needs_transportation = models.BooleanField(default=False)
    needs_setup = models.BooleanField(default=False)
    
    # Costs
    item_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    transport_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    tech_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    return_datetime = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Booking {self.id} by {self.customer.username} for {self.item.name}"

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.username}: {self.message[:20]}..."

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart for {self.user.username}"

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    item = models.ForeignKey(Inventory, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    
    # Rental Details
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    district = models.CharField(max_length=100, blank=True, null=True)
    venue = models.CharField(max_length=255, blank=True, null=True)
    needs_transportation = models.BooleanField(default=False)
    needs_setup = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.quantity} x {self.item.name} in {self.cart.user.username}'s Cart"