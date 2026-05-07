from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import CustomerSignupForm, OwnerSignupForm, InventoryForm, BookingForm, ProfileForm, UserUpdateForm, OwnerUpdateForm
from .models import Profile, Customer, Owner, Inventory, Booking, Notification
from datetime import datetime, timedelta
from decimal import Decimal

def logout_view(request):
    logout(request)
    messages.info(request, "You have been successfully logged out.")
    return redirect('home')

# 🔹 Role selection page
def role_select(request):
    return render(request, 'events/role_select.html')


def signup_customer(request):
    form = CustomerSignupForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():

            email = form.cleaned_data['email']

            # 🔹 Prevent duplicate BEFORE hitting DB
            if User.objects.filter(username=email).exists():
                form.add_error('email', 'Email already registered')
                return render(request, 'events/signup_customer.html', {'form': form})

            try:
                user = User.objects.create_user(
                    username=email,
                    email=email,
                    password=form.cleaned_data['password'],
                    first_name=form.cleaned_data['first_name'],
                    last_name=form.cleaned_data['last_name'],
                )

                # assign role
                user.profile.role = 'customer'
                user.profile.save()

                # save customer data
                Customer.objects.create(
                    user=user,
                    phone=form.cleaned_data['phone']
                )

                login(request, user)
                return redirect('dashboard')

            except IntegrityError:
                form.add_error(None, "Something went wrong. Try again.")

        else:
            print(form.errors)

    return render(request, 'events/signup_customer.html', {'form': form})


def signup_owner(request):
    form = OwnerSignupForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():

            email = form.cleaned_data['email']

            if User.objects.filter(username=email).exists():
                form.add_error('email', 'Email already registered')
                return render(request, 'events/signup_owner.html', {'form': form})

            user = User.objects.create_user(
                username=email,
                email=email,
                password=form.cleaned_data['password'],
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
            )

            # role
            user.profile.role = 'owner'
            user.profile.save()

            # owner details
            Owner.objects.create(
                user=user,
                company_name=form.cleaned_data['company_name'],
                business_type=form.cleaned_data['service_type'],
                location=form.cleaned_data['location'],
                state=form.cleaned_data['state'],
                district=form.cleaned_data['district'],
                license_id=form.cleaned_data['license_id'],
                phone=form.cleaned_data['phone'],
            )

            login(request, user)
            return redirect('dashboard')

    return render(request, 'events/signup_owner.html', {'form': form})


# 🔹 Dashboard (future use)
@login_required
def dashboard(request):
    try:
        role = request.user.profile.role
    except Exception:
        # If no profile exists (e.g. createsuperuser), create one automatically
        if request.user.is_superuser:
            from .models import Profile
            Profile.objects.get_or_create(user=request.user, defaults={'role': 'admin'})
            role = 'admin'
        else:
            from .models import Profile
            Profile.objects.get_or_create(user=request.user, defaults={'role': 'customer'})
            role = 'customer'

    if role == 'owner':
        owner, created = Owner.objects.get_or_create(user=request.user)
        pending_bookings = Booking.objects.filter(item__owner=owner, status='Pending')
        all_bookings = Booking.objects.filter(item__owner=owner).exclude(status='Pending')
        total_inventory_count = Inventory.objects.filter(owner=owner).count()
        active_orders_count = Booking.objects.filter(item__owner=owner, status='Approved').count()
        return render(request, 'events/owner_dashboard.html', {
            'pending_bookings': pending_bookings,
            'all_bookings': all_bookings,
            'total_inventory_count': total_inventory_count,
            'active_orders_count': active_orders_count
        })
    elif role == 'admin':
        # 🛡️ Safety Pre-flight: Ensure every user has a Profile record
        from .models import Profile
        all_users = User.objects.all()
        for u in all_users:
            if not hasattr(u, 'profile'):
                r = 'admin' if u.is_superuser else 'customer'
                Profile.objects.create(user=u, role=r)

        users = User.objects.all().order_by('-date_joined')
        owners = Owner.objects.select_related('user').all().order_by('company_name')
        customers = Customer.objects.select_related('user').all().order_by('user__username')
        inventory = Inventory.objects.select_related('owner__user').all().order_by('-id')
        bookings = Booking.objects.select_related('item', 'customer').all().order_by('-created_at')
        
        return render(request, 'events/admin_dashboard.html', {
            'users': users,
            'owners': owners,
            'customers': customers,
            'inventory': inventory,
            'bookings': bookings
        })
    else:
        bookings = Booking.objects.filter(customer=request.user)
        return render(request, 'events/customer_dashboard.html', {'bookings': bookings})
    

def home(request):
    return render(request, 'events/home.html')

@login_required
def add_inventory(request):
    if request.user.profile.role != 'owner':
        messages.error(request, "Access denied. Only owners can add inventory.")
        return redirect('dashboard')
        
    try:
        owner = Owner.objects.get(user=request.user)
    except Owner.DoesNotExist:
        messages.error(request, "Owner profile not found. Please complete your registration.")
        return redirect('dashboard')

    form = InventoryForm(request.POST or None, request.FILES or None)
    if request.method == "POST":
        if form.is_valid():
            inventory = form.save(commit=False)
            inventory.owner = owner
            inventory.save()
            return redirect('dashboard')

    return render(request, 'events/add_inventory.html', {'form': form})

@login_required
def inventory_list(request):
    if request.user.profile.role != 'owner':
        messages.error(request, "Access denied.")
        return redirect('dashboard')

    try:
        owner = Owner.objects.get(user=request.user)
    except Owner.DoesNotExist:
        messages.error(request, "Owner profile not found.")
        return redirect('dashboard')
        
    items = Inventory.objects.filter(owner=owner)
    return render(request, 'events/inventory_list.html', {'items': items})

@login_required
def edit_inventory(request, item_id):
    item = get_object_or_404(Inventory, id=item_id, owner__user=request.user)
    form = InventoryForm(request.POST or None, request.FILES or None, instance=item)
    
    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, "Inventory item updated successfully!")
            return redirect('inventory_list')
            
    return render(request, 'events/edit_inventory.html', {'form': form, 'item': item})

@login_required
def delete_inventory(request, item_id):
    item = get_object_or_404(Inventory, id=item_id, owner__user=request.user)
    if request.method == "POST":
        item.delete()
        messages.success(request, "Inventory item deleted successfully!")
    return redirect('inventory_list')

@login_required
def browse_inventory(request):
    items = Inventory.objects.filter(status='Available')
    return render(request, 'events/browse_inventory.html', {'items': items})

@login_required
def book_item(request, item_id):
    item = get_object_or_404(Inventory, id=item_id)
    
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            quantity = form.cleaned_data['quantity']
            if quantity > item.quantity:
                messages.error(request, f"Only {item.quantity} units available.")
            else:
                booking = form.save(commit=False)
                booking.customer = request.user
                booking.item = item
                
                # Calculation Logic
                quantity = booking.quantity
                
                # Days Calculation
                days = 1
                if booking.start_date and booking.end_date:
                    delta = booking.end_date - booking.start_date
                    days = delta.days + 1
                    if days < 1: days = 1

                booking.item_price = item.price_per_day * quantity * days
                
                # Transport Cost
                if booking.needs_transportation:
                    # Check if district matches owner's district
                    if booking.district and booking.district.lower() == item.owner.district.lower():
                        booking.transport_cost = Decimal('1000.00')
                    else:
                        booking.transport_cost = Decimal('2500.00') # Standard outside district rate
                
                # Tech Support (Setup) Cost
                if booking.needs_setup:
                    if item.category == 'sound':
                        booking.tech_cost = Decimal('1500.00') # Sound Engineer + Helper
                    elif item.category == 'light':
                        booking.tech_cost = Decimal('1500.00') # Light Engineer + Helper
                    else:
                        booking.tech_cost = Decimal('800.00') # Basic helper for LED/SFX
                
                booking.total_price = booking.item_price + booking.transport_cost + booking.tech_cost
                booking.save()
                
                messages.success(request, f"Booking request submitted! Total estimated cost: ₹{booking.total_price}")
                return redirect('dashboard')
    else:
        form = BookingForm()
    
    return render(request, 'events/book_item.html', {'form': form, 'item': item})

@login_required
def manage_booking(request, booking_id, action):
    booking = get_object_or_404(Booking, id=booking_id)
    
    # Ensure only the owner of the item can manage the booking
    if getattr(request.user, 'owner', None) == booking.item.owner:
        if action == 'approve':
            booking.status = 'Approved'
            booking.save()
            # Create notification for customer
            Notification.objects.create(
                user=booking.customer,
                message=f"Your booking for {booking.item.name} has been APPROVED by {booking.item.owner.company_name}."
            )
            
            # Send Email Confirmation
            try:
                subject = f'Booking Confirmed: {booking.item.name}'
                
                # Construct dynamic details for Transportation and Tech Support
                transport_details = ""
                if booking.needs_transportation:
                    transport_details = f"\nTRANSPORTATION DETAILS:\n" \
                                       f"- Service: Requested\n" \
                                       f"- Delivery to: {booking.venue}, {booking.district}\n" \
                                       f"- Driver Contact: {booking.item.owner.phone} (Main Office)\n"
                
                tech_details = ""
                if booking.needs_setup:
                    tech_details = f"\nTECH SUPPORT DETAILS:\n" \
                                   f"- Support Level: {booking.item.category.capitalize()} Engineer Provided\n" \
                                   f"- Technician Contact: {booking.item.owner.phone} (Lead Tech)\n"

                message = f'Hi {booking.customer.username},\n\n' \
                          f'Great news! Your booking request for {booking.item.name} has been accepted by {booking.item.owner.company_name}.\n\n' \
                          f'BOOKING SUMMARY:\n' \
                          f'- Item: {booking.item.name}\n' \
                          f'- Quantity: {booking.quantity}\n' \
                          f'- Duration: {booking.start_date} to {booking.end_date}\n' \
                          f'- Venue: {booking.venue}\n' \
                          f'- Total Price: ₹{booking.total_price}\n' \
                          f'{transport_details}' \
                          f'{tech_details}\n' \
                          f'For any immediate assistance, please contact the owner at {booking.item.owner.phone}.\n\n' \
                          f'Thank you for using StageKit Manager!'
                
                recipient_list = [booking.customer.email]
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list)
            except Exception as e:
                print(f"Error sending email: {e}")

            messages.success(request, f"Booking {booking.id} approved and confirmation email sent.")
        elif action == 'reject':
            booking.status = 'Rejected'
            booking.save()
            # Create notification for customer
            Notification.objects.create(
                user=booking.customer,
                message=f"Your booking for {booking.item.name} has been REJECTED by {booking.item.owner.company_name}."
            )
            messages.success(request, f"Booking {booking.id} rejected.")
    
    return redirect('dashboard')

from django.core.mail import send_mail
from django.utils import timezone
import random

def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            profile = user.profile
            # Generate 6 digit OTP
            otp = str(random.randint(100000, 999999))
            profile.otp = otp
            profile.otp_created_at = timezone.now()
            profile.save()
            
            # Send Email
            try:
                send_mail(
                    'Your StageKit OTP',
                    f'Your OTP for password reset is: {otp}. It is valid for 10 minutes.',
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=False,
                )
            except Exception as e:
                # If email fails, display the OTP in the message for testing purposes since it's a dev environment without real email setup yet.
                messages.error(request, f"Email failed to send. Developer mode OTP: {otp}")
            return redirect('verify_otp', email=email)
        except User.DoesNotExist:
            messages.error(request, "No user found with this email.")
    return render(request, 'events/forgot_password.html')

def verify_otp(request, email):
    if request.method == 'POST':
        otp_entered = request.POST.get('otp')
        try:
            user = User.objects.get(email=email)
            profile = user.profile
            
            if profile.otp == otp_entered:
                # Check expiration (10 mins)
                time_diff = timezone.now() - profile.otp_created_at
                if time_diff.total_seconds() < 600:
                    return redirect('reset_password', email=email)
                else:
                    messages.error(request, "OTP has expired.")
            else:
                messages.error(request, "Invalid OTP.")
        except User.DoesNotExist:
            pass
    return render(request, 'events/verify_otp.html', {'email': email})

def reset_password(request, email):
    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        if new_password == confirm_password:
            try:
                user = User.objects.get(email=email)
                user.set_password(new_password)
                user.save()
                
                # Clear OTP
                user.profile.otp = None
                user.profile.save()
                
                messages.success(request, "Password successfully reset! You can now login.")
                return redirect('login')
            except User.DoesNotExist:
                pass
        else:
            messages.error(request, "Passwords do not match.")
    return render(request, 'events/reset_password.html', {'email': email})

@login_required
def delete_user(request, user_id):
    if not request.user.profile.role == 'admin':
        messages.error(request, "Permission denied")
        return redirect('dashboard')
    
    user_to_delete = get_object_or_404(User, id=user_id)
    
    if user_to_delete == request.user:
        messages.error(request, "You cannot delete yourself")
        return redirect('dashboard')
        
    username = user_to_delete.username
    user_to_delete.delete()
    messages.success(request, f"User {username} deleted successfully")
    return redirect('dashboard')

@login_required
def admin_delete_inventory(request, item_id):
    if not request.user.profile.role == 'admin':
        messages.error(request, "Permission denied")
        return redirect('dashboard')
    
    item = get_object_or_404(Inventory, id=item_id)
    
    if request.method == "POST":
        item_name = item.name
        # 🛡️ Safe lookup for Owner Email
        owner_email = None
        if item.owner and item.owner.user:
            owner_email = item.owner.user.email

        if owner_email:
            try:
                subject = f"Notice: Item '{item_name}' has been removed"
                message = f"Hello,\n\nDue to some issues your item '{item_name}' has been removed by the admin from StageKit Manager.\n\nThank you."
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [owner_email])
            except Exception as e:
                print(f"Email error: {e}")
            
        item.delete()
        messages.success(request, f"Item '{item_name}' deleted successfully.")
    return redirect('dashboard')

@login_required
def admin_delete_booking(request, booking_id):
    if not request.user.profile.role == 'admin':
        messages.error(request, "Permission denied")
        return redirect('dashboard')
    
    booking = get_object_or_404(Booking, id=booking_id)
    
    if request.method == "POST":
        item_name = booking.item.name if booking.item else "Unknown Item"
        # 🛡️ Safe lookup for Customer Email
        customer_email = None
        if booking.customer:
            customer_email = booking.customer.email

        if customer_email:
            try:
                subject = f"Notice: Your booking for '{item_name}' has been cancelled"
                message = f"Hello,\n\nDue to some issues your booking for '{item_name}' has been removed by the admin from StageKit Manager.\n\nThank you."
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [customer_email])
            except Exception as e:
                print(f"Email error: {e}")
            
        booking.delete()
        messages.success(request, f"Booking for '{item_name}' deleted successfully.")
    return redirect('dashboard')

@login_required
def booking_requests(request):
    if request.user.profile.role != 'owner':
        return redirect('dashboard')
    
    owner = get_object_or_404(Owner, user=request.user)
    requests = Booking.objects.filter(item__owner=owner, status='Pending').order_by('-created_at')
    return render(request, 'events/booking_requests.html', {'requests': requests})

@login_required
def active_bookings(request):
    if request.user.profile.role != 'owner':
        return redirect('dashboard')
    
    owner = get_object_or_404(Owner, user=request.user)
    bookings = Booking.objects.filter(item__owner=owner, status='Approved').order_by('start_date')
    return render(request, 'events/active_bookings.html', {'bookings': bookings})

@login_required
def return_reminders(request):
    if request.user.profile.role != 'owner':
        return redirect('dashboard')
    
    owner = get_object_or_404(Owner, user=request.user)
    now = timezone.now()
    threshold = now + timedelta(hours=12)
    
    # Show items that should be returned within the next 12 hours
    reminders = Booking.objects.filter(
        item__owner=owner, 
        status='Approved',
        return_datetime__lte=threshold,
        return_datetime__gte=now
    ).order_by('return_datetime')
    
    return render(request, 'events/return_reminders.html', {'reminders': reminders})

@login_required
def customer_bookings(request):
    bookings = Booking.objects.filter(customer=request.user, status='Approved').order_by('start_date')
    return render(request, 'events/customer_bookings.html', {'bookings': bookings})

@login_required
def customer_pending(request):
    requests = Booking.objects.filter(customer=request.user, status='Pending').order_by('-created_at')
    return render(request, 'events/customer_pending.html', {'requests': requests})

@login_required
def customer_history(request):
    history = Booking.objects.filter(customer=request.user, status__in=['Completed', 'Rejected']).order_by('-start_date')
    return render(request, 'events/customer_history.html', {'history': history})

@login_required
def edit_profile(request):
    is_owner = request.user.profile.role == 'owner'
    
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileForm(request.POST, request.FILES, instance=request.user.profile)
        
        o_form = None
        if is_owner:
            owner_instance = get_object_or_404(Owner, user=request.user)
            o_form = OwnerUpdateForm(request.POST, instance=owner_instance)
        
        if u_form.is_valid() and p_form.is_valid():
            if is_owner and not o_form.is_valid():
                # If owner form is invalid, don't save anything yet
                pass
            else:
                u_form.save()
                p_form.save()
                if is_owner:
                    o_form.save()
                messages.success(request, "Your profile has been updated!")
                return redirect('dashboard')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileForm(instance=request.user.profile)
        o_form = None
        if is_owner:
            owner_instance = get_object_or_404(Owner, user=request.user)
            o_form = OwnerUpdateForm(instance=owner_instance)
    
    context = {
        'u_form': u_form,
        'p_form': p_form,
        'o_form': o_form,
        'is_owner': is_owner
    }
    return render(request, 'events/edit_profile.html', context)

@login_required
def notifications(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    # Mark all as read when viewing the page
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return render(request, 'events/notifications.html', {'notifications': notifications})
