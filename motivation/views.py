from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import Product, Purchase, Cart
from users.models import User
from assignments.models import Submission
from django.db.models import Sum, F, Value
from django.db.models.functions import Coalesce

def is_admin(user):
    return getattr(user, 'is_admin', False)

@login_required
def student_store(request):
    products = Product.objects.all().order_by('-created_at')
    # Покупки, которые не получены (корзина)
    cart_purchases = Purchase.objects.filter(student=request.user, received=False).select_related('product')
    purchases = Purchase.objects.filter(student=request.user)
    points = request.user.submissions.aggregate(total=Sum('points'))['total'] or 0
    spent = purchases.aggregate(total=Sum('product__price'))['total'] or 0
    available = points - spent

    if request.method == 'POST' and 'buy_product_id' in request.POST:
        product = get_object_or_404(Product, id=request.POST['buy_product_id'])
        if available >= product.price:
            Purchase.objects.create(student=request.user, product=product)
            messages.success(request, f'Товар "{product.name}" куплен!')
        else:
            messages.error(request, 'Недостаточно коинов!')
        return redirect('motivation:student_store')
    return render(request, 'motivation/student_store.html', {
        'products': products,
        'cart_purchases': cart_purchases,
        'points': available,
        'purchases': purchases
    })

@login_required
@user_passes_test(is_admin)
def admin_store(request):
    products = Product.objects.all().order_by('-created_at')
    students = User.objects.filter(user_type='student')
    purchases = Purchase.objects.select_related('student', 'product').order_by('-purchased_at')
    # Для каждого студента считаем points и spent, и available_points
    student_data = []
    for student in students:
        points = student.submissions.aggregate(total=Sum('points'))['total'] or 0
        spent = Purchase.objects.filter(student=student).aggregate(total=Sum('product__price'))['total'] or 0
        available = points - spent
        student_data.append({
            'student': student,
            'available_points': available
        })
    purchases_in_cart = Purchase.objects.filter(received=False).select_related('student', 'product')
    if request.method == 'POST':
        if 'delete_product_id' in request.POST:
            Product.objects.filter(id=request.POST['delete_product_id']).delete()
            messages.success(request, 'Товар удалён')
            return redirect('motivation:admin_store')
    return render(request, 'motivation/admin_store.html', {
        'products': products,
        'students_data': student_data,
        'purchases': purchases,
        'purchases_in_cart': purchases_in_cart
    })

@login_required
@user_passes_test(is_admin)
def product_create(request):
    if request.method == 'POST':
        name = request.POST['name']
        description = request.POST.get('description', '')
        price = int(request.POST['price'])
        image = request.FILES.get('image')
        Product.objects.create(name=name, description=description, price=price, image=image)
        messages.success(request, 'Товар создан')
        return redirect('motivation:admin_store')
    return render(request, 'motivation/product_create.html')

@login_required
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'motivation/product_detail.html', {'product': product})

@login_required
def cart_view(request):
    # Показываем только не полученные товары
    purchases = Purchase.objects.filter(student=request.user, received=False).select_related('product')
    if request.method == 'POST' and 'receive_purchase_id' in request.POST:
        purchase = get_object_or_404(Purchase, id=request.POST['receive_purchase_id'], student=request.user)
        purchase.received = True
        purchase.save()
        messages.success(request, 'Товар отмечен как полученный!')
        return redirect('motivation:cart')
    return render(request, 'motivation/cart.html', {'purchases': purchases})

@login_required
@user_passes_test(is_admin)
def admin_cart(request):
    purchases = Purchase.objects.filter(received=False).select_related('product', 'student')
    if request.method == 'POST' and 'receive_purchase_id' in request.POST:
        purchase = get_object_or_404(Purchase, id=request.POST['receive_purchase_id'])
        purchase.received = True
        purchase.save()
        messages.success(request, 'Товар отмечен как выданный!')
        return redirect('motivation:admin_cart')
    return render(request, 'motivation/admin_cart.html', {'purchases': purchases})


@login_required
@user_passes_test(is_admin)
def admin_students(request):
    students = User.objects.filter(user_type='student')
    student_data = []
    for student in students:
        points = student.submissions.aggregate(total=Sum('points'))['total'] or 0
        spent = Purchase.objects.filter(student=student).aggregate(total=Sum('product__price'))['total'] or 0
        available = points - spent
        student_data.append({
            'student': student,
            'available_points': available
        })
    return render(request, 'motivation/admin_students.html', {
        'students_data': student_data,
        'count': len(student_data)
    })

@login_required
@user_passes_test(is_admin)
def admin_purchases(request):
    purchases = Purchase.objects.select_related('student', 'product').order_by('-purchased_at')
    return render(request, 'motivation/admin_purchases.html', {
        'purchases': purchases,
        'count': purchases.count()
    })