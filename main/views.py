from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
from django.core.paginator import Paginator
from .models import Doctor, Patient, Specialization, Payment
from .forms import PaymentForm
import uuid

def home(request):
    popular_services = Specialization.objects.annotate(
        doctor_count=Count('doctor')
    ).order_by('-doctor_count', 'name')[:4]
    context = {
        'popular_services': popular_services,
        'popular_directions': ['Акушерство-гинекология', 'Кардиология', 'Неврология', 'Дерматология'],
    }
    return render(request, 'pages/home.html', context)

def doctors_list(request):
    doctors = Doctor.objects.all()
    specializations = Specialization.objects.all()
    
    # Поиск
    search_query = request.GET.get('search', '')
    if search_query:
        doctors = doctors.filter(Q(name__icontains=search_query) | Q(specialization__name__icontains=search_query))
    
    # Фильтрация по специализации
    selected_specialization = request.GET.get('specialization', '')
    if selected_specialization:
        doctors = doctors.filter(specialization_id=selected_specialization)
    
    # Сортировка
    selected_sort = request.GET.get('sort', 'name')
    valid_sorts = ['name', '-name', 'experience', '-experience', 'created_at', '-created_at']
    if selected_sort not in valid_sorts:
        selected_sort = 'name'
    doctors = doctors.order_by(selected_sort)
    
    # Пагинация
    paginator = Paginator(doctors, 12)
    page_number = request.GET.get('page', 1)
    doctors = paginator.get_page(page_number)
    
    context = {
        'doctors': doctors,
        'specializations': specializations,
        'search_query': search_query,
        'selected_specialization': selected_specialization,
        'selected_sort': selected_sort,
    }
    return render(request, 'pages/doctors_list.html', context)

def doctor_detail(request, id):
    doctor = get_object_or_404(Doctor, id=id)
    is_this_doctor = False
    if request.user.is_authenticated and hasattr(request.user, 'doctor_profile'):
        is_this_doctor = (request.user.doctor_profile.id == doctor.id)
    return render(request, 'pages/doctor_detail.html', {'doctor': doctor, 'is_this_doctor': is_this_doctor})
def clinics(request):
    return render(request, 'pages/clinics.html', {'title': 'Клиники'})

def promotions(request):
    return render(request, 'pages/promotions.html', {'title': 'Акции'})

def services(request):
    services = Specialization.objects.all().order_by('name')
    popular_services = services.annotate(doctor_count=Count('doctor')).order_by('-doctor_count', 'name')[:4]
    return render(request, 'pages/services.html', {
        'title': 'Услуги',
        'services': services,
        'popular_services': popular_services,
    })


def online_payment(request):
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.transaction_id = 'TR' + uuid.uuid4().hex[:12].upper()
            # Симулируем успешную оплату
            payment.status = 'paid'
            payment.save()
            return redirect('payment_success', tx=payment.transaction_id)
    else:
        form = PaymentForm()
    return render(request, 'pages/payment.html', {'form': form})


def payment_success(request, tx):
    payment = get_object_or_404(Payment, transaction_id=tx)
    return render(request, 'pages/payment_success.html', {'payment': payment})

def clinic_logout_view(request):
    logout(request)
    return redirect('home')