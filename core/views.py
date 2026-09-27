from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import logout
from django.db.models import Sum, Count
from django.utils import timezone
from .models import Sale, Participant, Tree, TreeRequest, ExpenseCategory, SaleExpense
from .forms import (
    SaleForm, ParticipantForm, TreeForm, TreeRequestForm, EditTreeRequestForm,
    ConfirmRequestForm, ExpenseCategoryForm,
    SaleTreeFormSet, SaleExpenseFormSet
)


def is_admin(user):
    return user.is_superuser or user.is_staff


@login_required
def index(request):
    if is_admin(request.user):
        total_sales_weight = Sale.objects.aggregate(total=Sum('weight_kg'))['total'] or 0
        total_sales_value = Sale.objects.aggregate(total=Sum('total_price'))['total'] or 0

        total_trees_cost = 0
        total_expenses_cost = 0
        for sale in Sale.objects.all():
            total_trees_cost += sale.get_trees_total_cost()
            total_expenses_cost += sale.get_expenses_total_cost()

        total_all_expenses = total_trees_cost + total_expenses_cost
        remaining_balance = total_sales_value - total_all_expenses
        total_participants = Participant.objects.filter(is_active=True).count()

        pending_requests = TreeRequest.objects.filter(status='pending').count()
        purchased_requests = TreeRequest.objects.filter(status='purchased').count()
        ready_requests = TreeRequest.objects.filter(status='ready').count()
        completed_requests = TreeRequest.objects.filter(status='completed').count()

        recent_sales = Sale.objects.all()[:5]
        active_requests = TreeRequest.objects.filter(
            status__in=['pending', 'purchased', 'ready']
        ).order_by('position')[:10]

        context = {
            'total_sales_weight': total_sales_weight,
            'total_sales_value': total_sales_value,
            'total_trees_cost': total_trees_cost,
            'total_expenses_cost': total_expenses_cost,
            'total_all_expenses': total_all_expenses,
            'remaining_balance': remaining_balance,
            'total_participants': total_participants,
            'pending_requests': pending_requests,
            'purchased_requests': purchased_requests,
            'ready_requests': ready_requests,
            'completed_requests': completed_requests,
            'recent_sales': recent_sales,
            'active_requests': active_requests,
            'is_admin': True,
        }
        return render(request, 'core/index.html', context)
    else:
        total_participants = Participant.objects.filter(is_active=True).count()
        pending_requests = TreeRequest.objects.filter(status='pending').count()
        context = {
            'total_participants': total_participants,
            'pending_requests': pending_requests,
            'is_admin': False,
        }
        return render(request, 'core/index_user.html', context)


# ============ المبيعات ============

@login_required
@user_passes_test(is_admin, login_url='/', redirect_field_name=None)
def add_sale(request):
    if request.method == 'POST':
        form = SaleForm(request.POST)
        if form.is_valid():
            sale = form.save(commit=False)
            sale.participant = None
            sale.save()

            tree_formset = SaleTreeFormSet(request.POST, instance=sale, prefix='trees')
            expense_formset = SaleExpenseFormSet(request.POST, instance=sale, prefix='expenses')

            if tree_formset.is_valid() and expense_formset.is_valid():
                tree_formset.save()
                expense_formset.save()
                messages.success(request, 'تم إضافة عملية البيع بنجاح!')
                return redirect('/sale/add/')
    else:
        form = SaleForm()
        tree_formset = SaleTreeFormSet(prefix='trees')
        expense_formset = SaleExpenseFormSet(prefix='expenses')

    sales = Sale.objects.all().order_by('-sale_date')

    total_sales_weight = Sale.objects.aggregate(total=Sum('weight_kg'))['total'] or 0
    total_sales_value = Sale.objects.aggregate(total=Sum('total_price'))['total'] or 0

    total_trees_cost = 0
    total_expenses_cost = 0
    for sale_obj in Sale.objects.all():
        total_trees_cost += sale_obj.get_trees_total_cost()
        total_expenses_cost += sale_obj.get_expenses_total_cost()

    total_all_expenses = total_trees_cost + total_expenses_cost
    remaining_balance = total_sales_value - total_all_expenses

    context = {
        'form': form,
        'tree_formset': tree_formset,
        'expense_formset': expense_formset,
        'sales': sales,
        'total_sales_weight': total_sales_weight,
        'total_sales_value': total_sales_value,
        'total_trees_cost': total_trees_cost,
        'total_expenses_cost': total_expenses_cost,
        'total_all_expenses': total_all_expenses,
        'remaining_balance': remaining_balance,
    }
    return render(request, 'core/add_sale.html', context)


@login_required
@user_passes_test(is_admin, login_url='/', redirect_field_name=None)
def edit_sale(request, pk):
    sale = get_object_or_404(Sale, pk=pk)

    if request.method == 'POST':
        form = SaleForm(request.POST, instance=sale)
        if form.is_valid():
            sale = form.save(commit=False)
            sale.participant = None
            sale.save()

            tree_formset = SaleTreeFormSet(request.POST, instance=sale, prefix='trees')
            expense_formset = SaleExpenseFormSet(request.POST, instance=sale, prefix='expenses')

            if tree_formset.is_valid() and expense_formset.is_valid():
                tree_formset.save()
                expense_formset.save()
                messages.success(request, 'تم تعديل عملية البيع بنجاح!')
                return redirect('/sale/add/')
    else:
        form = SaleForm(instance=sale)
        tree_formset = SaleTreeFormSet(instance=sale, prefix='trees')
        expense_formset = SaleExpenseFormSet(instance=sale, prefix='expenses')

    sales = Sale.objects.all().order_by('-sale_date')
    context = {
        'form': form,
        'tree_formset': tree_formset,
        'expense_formset': expense_formset,
        'sales': sales,
        'edit_mode': True,
        'edit_sale': sale,
    }
    return render(request, 'core/add_sale.html', context)


@login_required
@user_passes_test(is_admin, login_url='/', redirect_field_name=None)
def delete_sale(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    if request.method == 'POST':
        sale.delete()
        messages.success(request, 'تم حذف عملية البيع بنجاح!')
        return redirect('/sale/add/')
    return render(request, 'core/delete_sale.html', {'sale': sale})


@login_required
@user_passes_test(is_admin, login_url='/', redirect_field_name=None)
def sale_detail(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    context = {
        'sale': sale,
        'sale_trees': sale.saletree_set.all(),
        'sale_expenses': sale.saleexpense_set.all(),
        'trees_total': sale.get_trees_total_cost(),
        'expenses_total': sale.get_expenses_total_cost(),
        'all_expenses': sale.get_all_expenses(),
        'remaining': sale.get_remaining_amount(),
    }
    return render(request, 'core/sale_detail.html', context)


# ============ المشاركون ============

@login_required
def add_participant(request):
    if request.method == 'POST':
        form = ParticipantForm(request.POST)
        if form.is_valid():
            participant = form.save()
            messages.success(request, f'تم إضافة المشارك "{participant.name}" بنجاح!')
            return redirect('/participant/add/')
    else:
        form = ParticipantForm()

    participants = Participant.objects.all().order_by('-join_date')
    return render(request, 'core/add_participant.html', {
        'form': form,
        'participants': participants,
    })


@login_required
def edit_participant(request, pk):
    participant = get_object_or_404(Participant, pk=pk)
    if request.method == 'POST':
        form = ParticipantForm(request.POST, instance=participant)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تعديل بيانات المشارك بنجاح!')
            return redirect('/participant/add/')
    else:
        form = ParticipantForm(instance=participant)

    participants = Participant.objects.all().order_by('-join_date')
    return render(request, 'core/add_participant.html', {
        'form': form,
        'participants': participants,
        'edit_mode': True,
        'edit_participant': participant,
    })


@login_required
def delete_participant(request, pk):
    participant = get_object_or_404(Participant, pk=pk)
    if request.method == 'POST':
        participant.delete()
        messages.success(request, 'تم حذف المشارك بنجاح!')
        return redirect('/participant/add/')
    return render(request, 'core/delete_participant.html', {'participant': participant})


@login_required
def participant_detail(request, pk):
    participant = get_object_or_404(Participant, pk=pk)
    return render(request, 'core/participant_detail.html', {
        'participant': participant,
        'sales': participant.sale_set.all(),
        'requests': participant.treerequest_set.all().order_by('-request_date'),
        'total_weight': participant.get_total_plastic_weight(),
    })


# ============ الأشجار ============

@login_required
def add_tree(request):
    if request.method == 'POST':
        form = TreeForm(request.POST)
        if form.is_valid():
            tree = form.save()
            messages.success(request, f'تم إضافة الشجرة "{tree.tree_type}" بنجاح!')
            return redirect('/trees/')
    else:
        form = TreeForm()
    return render(request, 'core/add_tree.html', {
        'form': form,
        'trees': Tree.objects.all().order_by('tree_type'),
    })


@login_required
def tree_list(request):
    return render(request, 'core/tree_list.html', {
        'trees': Tree.objects.all().order_by('tree_type')
    })


@login_required
def edit_tree(request, pk):
    tree = get_object_or_404(Tree, pk=pk)
    if request.method == 'POST':
        form = TreeForm(request.POST, instance=tree)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تعديل الشجرة بنجاح!')
            return redirect('/trees/')
    else:
        form = TreeForm(instance=tree)
    return render(request, 'core/add_tree.html', {
        'form': form,
        'trees': Tree.objects.all().order_by('tree_type'),
        'edit_mode': True,
        'edit_tree': tree,
    })


@login_required
def delete_tree(request, pk):
    tree = get_object_or_404(Tree, pk=pk)
    if request.method == 'POST':
        tree.delete()
        messages.success(request, 'تم حذف الشجرة بنجاح!')
        return redirect('/trees/')
    return render(request, 'core/delete_tree.html', {'tree': tree})


# ============ أنواع المصروفات ============

@login_required
@user_passes_test(is_admin, login_url='/', redirect_field_name=None)
def add_expense_category(request):
    if request.method == 'POST':
        form = ExpenseCategoryForm(request.POST)
        if form.is_valid():
            cat = form.save()
            messages.success(request, f'تم إضافة نوع المصروف "{cat.name}" بنجاح!')
            return redirect('/expenses/categories/')
    else:
        form = ExpenseCategoryForm()
    return render(request, 'core/add_expense_category.html', {
        'form': form,
        'categories': ExpenseCategory.objects.all().order_by('name'),
    })


@login_required
@user_passes_test(is_admin, login_url='/', redirect_field_name=None)
def edit_expense_category(request, pk):
    cat = get_object_or_404(ExpenseCategory, pk=pk)
    if request.method == 'POST':
        form = ExpenseCategoryForm(request.POST, instance=cat)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تعديل نوع المصروف بنجاح!')
            return redirect('/expenses/categories/')
    else:
        form = ExpenseCategoryForm(instance=cat)
    return render(request, 'core/add_expense_category.html', {
        'form': form,
        'categories': ExpenseCategory.objects.all().order_by('name'),
        'edit_mode': True,
        'edit_category': cat,
    })


@login_required
@user_passes_test(is_admin, login_url='/', redirect_field_name=None)
def delete_expense_category(request, pk):
    cat = get_object_or_404(ExpenseCategory, pk=pk)
    if request.method == 'POST':
        cat.delete()
        messages.success(request, 'تم حذف نوع المصروف بنجاح!')
        return redirect('/expenses/categories/')
    return render(request, 'core/delete_expense_category.html', {'category': cat})


# ============ طلبات الأشجار ============

@login_required
def add_tree_request(request):
    if request.method == 'POST':
        form = TreeRequestForm(request.POST)
        if form.is_valid():
            tree_request = form.save()
            messages.success(request, f'تم إضافة طلب الشجرة بنجاح! رقم الدور: {tree_request.position}')
            return redirect('/requests/')
    else:
        form = TreeRequestForm()
    return render(request, 'core/add_tree_request.html', {'form': form})


@login_required
def tree_requests_list(request):
    """قائمة الطلبات الكاملة - للأدمن فقط"""
    if not is_admin(request.user):
        messages.warning(request, 'ليس لديك صلاحية لعرض هذه الصفحة')
        return redirect('/')

    return render(request, 'core/tree_requests_list.html', {
        'pending_requests': TreeRequest.objects.filter(status='pending').order_by('position'),
        'purchased_requests': TreeRequest.objects.filter(status='purchased').order_by('position'),
        'ready_requests': TreeRequest.objects.filter(status='ready').order_by('position'),
        'completed_requests': TreeRequest.objects.filter(status='completed').order_by('-completed_date'),
        'cancelled_requests': TreeRequest.objects.filter(status='cancelled').order_by('-request_date'),
    })


@login_required
@user_passes_test(is_admin, login_url='/', redirect_field_name=None)
def edit_tree_request(request, pk):
    """تعديل نوع الشجرة في الطلب مع الحفاظ على رقم الدور"""
    tree_request = get_object_or_404(TreeRequest, pk=pk)

    if tree_request.status not in ['pending', 'purchased', 'ready']:
        messages.warning(request, 'لا يمكن تعديل هذا الطلب في حالته الحالية')
        return redirect('/requests/')

    if request.method == 'POST':
        old_tree = tree_request.tree
        form = EditTreeRequestForm(request.POST, instance=tree_request)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f'تم تعديل طلب {tree_request.participant.name}: من "{old_tree}" إلى "{tree_request.tree}" - رقم الدور محفوظ: {tree_request.position}'
            )
            return redirect('/requests/')
    else:
        form = EditTreeRequestForm(instance=tree_request)

    return render(request, 'core/edit_tree_request.html', {
        'form': form,
        'tree_request': tree_request,
    })


@login_required
@user_passes_test(is_admin, login_url='/', redirect_field_name=None)
def mark_purchased(request, pk):
    """تم شراء الشجرة من المشتل"""
    tree_request = get_object_or_404(TreeRequest, pk=pk)

    if tree_request.status != 'pending':
        messages.warning(request, 'لا يمكن تنفيذ هذا الإجراء على الطلب')
        return redirect('/requests/')

    if request.method == 'POST':
        tree_request.status = 'purchased'
        tree_request.purchased_date = timezone.now()
        tree_request.save()
        messages.success(request, f'تم تسجيل شراء شجرة "{tree_request.tree}" للمشارك {tree_request.participant.name}')
        return redirect('/requests/')

    return render(request, 'core/mark_purchased.html', {'tree_request': tree_request})


@login_required
@user_passes_test(is_admin, login_url='/', redirect_field_name=None)
def mark_ready(request, pk):
    """تجهيز الشجرة وإعطاء رقم تسليم"""
    tree_request = get_object_or_404(TreeRequest, pk=pk)

    if tree_request.status != 'purchased':
        messages.warning(request, 'يجب شراء الشجرة أولاً')
        return redirect('/requests/')

    if request.method == 'POST':
        tree_request.status = 'ready'
        tree_request.ready_date = timezone.now()
        if not tree_request.delivery_number:
            tree_request.generate_delivery_number()
        tree_request.save()
        messages.success(
            request,
            f'✅ الشجرة جاهزة للتسليم! رقم التسليم: {tree_request.delivery_number}'
        )
        return redirect('/requests/')

    return render(request, 'core/mark_ready.html', {'tree_request': tree_request})


@login_required
@user_passes_test(is_admin, login_url='/', redirect_field_name=None)
def confirm_request(request, pk):
    """تأكيد التسليم النهائي"""
    tree_request = get_object_or_404(TreeRequest, pk=pk)

    if tree_request.status != 'ready':
        messages.warning(request, 'الشجرة ليست جاهزة للتسليم')
        return redirect('/requests/')

    if request.method == 'POST':
        form = ConfirmRequestForm(request.POST)
        if form.is_valid():
            tree_request.status = 'completed'
            tree_request.completed_date = timezone.now()
            tree_request.notes = (tree_request.notes or '') + f'\nتم التسليم: {form.cleaned_data["notes"]}'
            tree_request.save()

            # إعادة ترتيب أرقام الدور للطلبات النشطة فقط
            next_requests = TreeRequest.objects.filter(
                position__gt=tree_request.position,
                status__in=['pending', 'purchased', 'ready']
            ).order_by('position')
            for req in next_requests:
                req.position -= 1
                req.save()

            messages.success(
                request,
                f'✅ تم تسليم الشجرة للمشارك {tree_request.participant.name} بنجاح!'
            )
            return redirect('/requests/')
    else:
        form = ConfirmRequestForm()

    return render(request, 'core/confirm_request.html', {
        'tree_request': tree_request, 'form': form
    })


@login_required
@user_passes_test(is_admin, login_url='/', redirect_field_name=None)
def cancel_request(request, pk):
    tree_request = get_object_or_404(TreeRequest, pk=pk)
    if tree_request.status == 'completed':
        messages.warning(request, 'لا يمكن إلغاء طلب مكتمل!')
        return redirect('/requests/')

    if request.method == 'POST':
        tree_request.status = 'cancelled'
        tree_request.save()

        next_requests = TreeRequest.objects.filter(
            position__gt=tree_request.position,
            status__in=['pending', 'purchased', 'ready']
        ).order_by('position')
        for req in next_requests:
            req.position -= 1
            req.save()

        messages.success(request, 'تم إلغاء الطلب بنجاح!')
        return redirect('/requests/')

    return render(request, 'core/cancel_request.html', {'tree_request': tree_request})


# ============ الإحصائيات ============

@login_required
@user_passes_test(is_admin, login_url='/', redirect_field_name=None)
def statistics(request):
    total_sales_weight = Sale.objects.aggregate(total=Sum('weight_kg'))['total'] or 0
    total_sales_value = Sale.objects.aggregate(total=Sum('total_price'))['total'] or 0

    total_trees_cost = 0
    total_expenses_cost = 0
    for sale in Sale.objects.all():
        total_trees_cost += sale.get_trees_total_cost()
        total_expenses_cost += sale.get_expenses_total_cost()

    total_all_expenses = total_trees_cost + total_expenses_cost
    remaining_balance = total_sales_value - total_all_expenses

    top_participants = Participant.objects.annotate(
        total_weight=Sum('sale__weight_kg'),
        total_requests=Count('treerequest')
    ).order_by('-total_weight')[:10]

    tree_distribution = TreeRequest.objects.filter(
        status='completed'
    ).values('tree__tree_type').annotate(
        count=Sum('quantity')
    ).order_by('-count')

    monthly_sales = Sale.objects.extra(
        select={'month': "strftime('%%Y-%%m', sale_date)"}
    ).values('month').annotate(
        total_weight=Sum('weight_kg'),
        total_value=Sum('total_price')
    ).order_by('month')

    return render(request, 'core/statistics.html', {
        'total_sales_weight': total_sales_weight,
        'total_sales_value': total_sales_value,
        'total_trees_cost': total_trees_cost,
        'total_expenses_cost': total_expenses_cost,
        'total_all_expenses': total_all_expenses,
        'remaining_balance': remaining_balance,
        'total_participants': Participant.objects.filter(is_active=True).count(),
        'total_trees_requested': TreeRequest.objects.filter(
            status='completed').aggregate(total=Sum('quantity'))['total'] or 0,
        'top_participants': top_participants,
        'tree_distribution': tree_distribution,
        'monthly_sales': monthly_sales,
    })


# ============ تسجيل الخروج ============

def logout_confirm(request):
    if request.method == 'POST':
        logout(request)
        return redirect('/accounts/login/')
    return render(request, 'core/logout_confirm.html')