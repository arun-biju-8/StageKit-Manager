from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),   # 👈 change this
    path('role/', views.role_select, name='role_select'),
    path('signup/customer/', views.signup_customer, name='signup_customer'),
    path('signup/owner/', views.signup_owner, name='signup_owner'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('inventory/add/', views.add_inventory, name='add_inventory'),
    path('inventory/edit/<int:item_id>/', views.edit_inventory, name='edit_inventory'),
    path('inventory/delete/<int:item_id>/', views.delete_inventory, name='delete_inventory'),
    path('inventory/', views.inventory_list, name='inventory_list'),
    path('browse/', views.browse_inventory, name='browse_inventory'),
    path('book/<int:item_id>/', views.book_item, name='book_item'),
    path('booking/<int:booking_id>/<str:action>/', views.manage_booking, name='manage_booking'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('verify-otp/<str:email>/', views.verify_otp, name='verify_otp'),
    path('reset-password/<str:email>/', views.reset_password, name='reset_password'),
    path('user/delete/<int:user_id>/', views.delete_user, name='delete_user'),
    path('owner/requests/', views.booking_requests, name='booking_requests'),
    path('owner/bookings/', views.active_bookings, name='active_bookings'),
    path('owner/reminders/', views.return_reminders, name='return_reminders'),
    path('customer/bookings/', views.customer_bookings, name='customer_bookings'),
    path('customer/pending/', views.customer_pending, name='customer_pending'),
    path('customer/history/', views.customer_history, name='customer_history'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('notifications/', views.notifications, name='notifications'),
    path('portal/inventory/delete/<int:item_id>/', views.admin_delete_inventory, name='admin_delete_inventory'),
    path('portal/booking/delete/<int:booking_id>/', views.admin_delete_booking, name='admin_delete_booking'),
]