from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum, Count
from django.utils import timezone
from .models import Sale, Participant, Tree, TreeRequest
from .forms import (
    SaleForm, ParticipantForm, TreeForm, TreeRequestForm, 
    ConfirmRequestForm, SaleTreeFormSet
)

def index(request):
    total_sales_weight = Sale.objects.aggregate(total=Sum('weight_kg'))['total'] or 0
    total_sales_value = Sale.objects.aggregate(total=Sum('total_price'))['total'] or 0
    
    # حساب إجمالي تكلفة الأشجار المشتراة
    total_trees_cost = 0
    for sale in Sale.objects.all():
        total_trees_cost += sale.get_trees_total_cost()
    
    remaining_balance = total_sales_value - total_trees_cost
    
    total_participants = Participant.objects.filter(is_active=True).count()
    pending_requests = TreeRequest.objects.filter(status='pending').count()
    completed_requests = TreeRequest.objects.filter(status='completed').count()
    recent_sales = Sale.objects.all()[:5]
    pending_requests_list = TreeRequest.objects.filter(
        status__in=['pending', 'in_progress']
    ).order_by('position')[:10]
    
    context = {
        'total_sales_weight': total_sales_weight,
        'total_sales_value': total_sales_value,
        'total_trees_cost': total_trees_cost,
        'remaining_balance': remaining_balance,
        'total_participants': total_participants,
        'pending_requests': pending_requests,
        'completed_requests': completed_requests,
        'recent_sales': recent_sales,
        'pending_requests_list': pending_requests_list,
    }
    return render(request, 'core/index.html', context)

def add_sale(request):
    """إضافة بيع جديد وعرض قائمة المبيعات"""
    if request.method == 'POST':
        form = SaleForm(request.POST)
        if form.is_valid():
            sale = form.save(commit=False)
            sale.participant = None
            sale.save()
            
            formset = SaleTreeFormSet(request.POST, instance=sale)
            if formset.is_valid():
                formset.save()
                messages.success(request, 'تم إضافة عملية البيع بنجاح!')
                return redirect('/sale/add/')  # البقاء في نفس الصفحة
    else:
        form = SaleForm()
        formset = SaleTreeFormSet()
    
    # جلب جميع المبيعات لعرضها في نفس الصفحة
    sales = Sale.objects.all().order_by('-sale_date')
    
    # حساب الإحصائيات
    total_sales_weight = Sale.objects.aggregate(total=Sum('weight_kg'))['total'] or 0
    total_sales_value = Sale.objects.aggregate(total=Sum('total_price'))['total'] or 0
    
    # حساب إجمالي تكلفة الأشجار
    total_trees_cost = 0
    for sale_obj in Sale.objects.all():
        total_trees_cost += sale_obj.get_trees_total_cost()
    
    remaining_balance = total_sales_value - total_trees_cost
    
    context = {
        'form': form,
        'formset': formset,
        'sales': sales,
        'total_sales_weight': total_sales_weight,
        'total_sales_value': total_sales_value,
        'total_trees_cost': total_trees_cost,
        'remaining_balance': remaining_balance,
        'title': 'إدارة المبيعات'
    }
    return render(request, 'core/add_sale.html', context)

def edit_sale(request, pk):
    """تعديل عملية بيع"""
    sale = get_object_or_404(Sale, pk=pk)
    
    if request.method == 'POST':
        form = SaleForm(request.POST, instance=sale)
        if form.is_valid():
            sale = form.save(commit=False)
            sale.participant = None
            sale.save()
            
            formset = SaleTreeFormSet(request.POST, instance=sale)
            if formset.is_valid():
                formset.save()
                messages.success(request, 'تم تعديل عملية البيع بنجاح!')
                return redirect('/sale/add/')
    else:
        form = SaleForm(instance=sale)
        formset = SaleTreeFormSet(instance=sale)
    
    sales = Sale.objects.all().order_by('-sale_date')
    context = {
        'form': form,
        'formset': formset,
        'sales': sales,
        'edit_mode': True,
        'edit_sale': sale,
        'title': 'تعديل عملية بيع'
    }
    return render(request, 'core/add_sale.html', context)

def delete_sale(request, pk):
    """حذف عملية بيع"""
    sale = get_object_or_404(Sale, pk=pk)
    sale_date = sale.sale_date
    sale_weight = sale.weight_kg
    
    if request.method == 'POST':
        sale.delete()
        messages.success(request, f'تم حذف عملية البيع بتاريخ {sale_date} بنجاح!')
        return redirect('/sale/add/')
    
    context = {
        'sale': sale,
        'title': 'تأكيد الحذف'
    }
    return render(request, 'core/delete_sale.html', context)
def sale_detail(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    sale_trees = sale.saletree_set.all()
    trees_total = sale.get_trees_total_cost()
    remaining = sale.get_remaining_amount()
    
    context = {
        'sale': sale,
        'sale_trees': sale_trees,
        'trees_total': trees_total,
        'remaining': remaining,
    }
    return render(request, 'core/sale_detail.html', context)

def add_participant(request):
    """إضافة مشارك جديد وعرض قائمة المشاركين"""
    if request.method == 'POST':
        form = ParticipantForm(request.POST)
        if form.is_valid():
            participant = form.save()
            messages.success(request, f'تم إضافة المشارك "{participant.name}" بنجاح!')
            return redirect('/participant/add/')  # البقاء في نفس الصفحة
    else:
        form = ParticipantForm()
    
    # جلب جميع المشاركين لعرضهم في نفس الصفحة
    participants = Participant.objects.all().order_by('-join_date')
    context = {
        'form': form,
        'participants': participants,
        'title': 'إدارة المشاركين'
    }
    return render(request, 'core/add_participant.html', context)

def edit_participant(request, pk):
    """تعديل بيانات مشارك"""
    participant = get_object_or_404(Participant, pk=pk)
    
    if request.method == 'POST':
        form = ParticipantForm(request.POST, instance=participant)
        if form.is_valid():
            form.save()
            messages.success(request, f'تم تعديل بيانات المشارك "{participant.name}" بنجاح!')
            return redirect('/participant/add/')
    else:
        form = ParticipantForm(instance=participant)
    
    participants = Participant.objects.all().order_by('-join_date')
    context = {
        'form': form,
        'participants': participants,
        'edit_mode': True,
        'edit_participant': participant,
        'title': 'تعديل بيانات مشارك'
    }
    return render(request, 'core/add_participant.html', context)

def delete_participant(request, pk):
    """حذف مشارك"""
    participant = get_object_or_404(Participant, pk=pk)
    participant_name = participant.name
    
    if request.method == 'POST':
        participant.delete()
        messages.success(request, f'تم حذف المشارك "{participant_name}" بنجاح!')
        return redirect('/participant/add/')
    
    context = {
        'participant': participant,
        'title': 'تأكيد الحذف'
    }
    return render(request, 'core/delete_participant.html', context)

def participant_detail(request, pk):
    participant = get_object_or_404(Participant, pk=pk)
    sales = participant.sale_set.all()
    requests = participant.treerequest_set.all().order_by('-request_date')
    total_weight = participant.get_total_plastic_weight()
    context = {
        'participant': participant,
        'sales': sales,
        'requests': requests,
        'total_weight': total_weight,
    }
    return render(request, 'core/participant_detail.html', context)

def add_tree(request):
    if request.method == 'POST':
        form = TreeForm(request.POST)
        if form.is_valid():
            tree = form.save()
            messages.success(request, f'تم إضافة نوع الشجرة "{tree.tree_type}" بنجاح!')
            return redirect('/trees/')
    else:
        form = TreeForm()
    
    # جلب جميع الأشجار لعرضها في نفس الصفحة
    trees = Tree.objects.all().order_by('tree_type')
    context = {
        'form': form,
        'trees': trees,
        'title': 'إدارة أنواع الأشجار'
    }
    return render(request, 'core/add_tree.html', context)

def edit_tree(request, pk):
    """تعديل نوع شجرة"""
    tree = get_object_or_404(Tree, pk=pk)
    
    if request.method == 'POST':
        form = TreeForm(request.POST, instance=tree)
        if form.is_valid():
            form.save()
            messages.success(request, f'تم تعديل نوع الشجرة "{tree.tree_type}" بنجاح!')
            return redirect('/trees/')
    else:
        form = TreeForm(instance=tree)
    
    trees = Tree.objects.all().order_by('tree_type')
    context = {
        'form': form,
        'trees': trees,
        'edit_mode': True,
        'edit_tree': tree,
        'title': 'تعديل نوع شجرة'
    }
    return render(request, 'core/add_tree.html', context)

def delete_tree(request, pk):
    """حذف نوع شجرة"""
    tree = get_object_or_404(Tree, pk=pk)
    tree_name = tree.tree_type
    
    if request.method == 'POST':
        tree.delete()
        messages.success(request, f'تم حذف نوع الشجرة "{tree_name}" بنجاح!')
        return redirect('/trees/')
    
    context = {
        'tree': tree,
        'title': 'تأكيد الحذف'
    }
    return render(request, 'core/delete_tree.html', context)
def tree_list(request):
    trees = Tree.objects.all().order_by('tree_type')
    context = {'trees': trees}
    return render(request, 'core/tree_list.html', context)

def add_tree_request(request):
    if request.method == 'POST':
        form = TreeRequestForm(request.POST)
        if form.is_valid():
            tree_request = form.save()
            messages.success(request, f'تم إضافة طلب الشجرة بنجاح! رقم الطلب: {tree_request.position}')
            return redirect('/requests/')  # استخدم المسار المباشر
    else:
        form = TreeRequestForm()
    context = {'form': form, 'title': 'طلب شجرة جديدة'}
    return render(request, 'core/add_tree_request.html', context)

def confirm_request(request, pk):
    tree_request = get_object_or_404(TreeRequest, pk=pk)
    
    if tree_request.status == 'completed':
        messages.warning(request, 'هذا الطلب مكتمل بالفعل!')
        return redirect('/requests/')
    
    if request.method == 'POST':
        form = ConfirmRequestForm(request.POST)
        if form.is_valid():
            trees_provided = form.cleaned_data['trees_provided']
            notes = form.cleaned_data['notes']
            
            tree_request.status = 'completed'
            tree_request.completed_date = timezone.now()
            tree_request.notes = (tree_request.notes or '') + f'\nتم الإكمال: {notes}'
            tree_request.save()
            
            # إعادة ترتيب الأرقام للطلبات التالية
            next_requests = TreeRequest.objects.filter(
                position__gt=tree_request.position,
                status='pending'  # فقط قيد الانتظار
            ).order_by('position')
            
            for req in next_requests:
                req.position = req.position - 1
                req.save()
            
            messages.success(request, 'تم تأكيد استلام الشجرة بنجاح!')
            return redirect('/requests/')
    else:
        form = ConfirmRequestForm(initial={'trees_provided': tree_request.quantity})
    
    context = {'tree_request': tree_request, 'form': form}
    return render(request, 'core/confirm_request.html', context)

def cancel_request(request, pk):
    tree_request = get_object_or_404(TreeRequest, pk=pk)
    
    if tree_request.status == 'completed':
        messages.warning(request, 'لا يمكن إلغاء طلب مكتمل!')
        return redirect('/requests/')
    
    if request.method == 'POST':
        tree_request.status = 'cancelled'
        tree_request.save()
        
        # إعادة ترتيب الأرقام للطلبات التالية
        next_requests = TreeRequest.objects.filter(
            position__gt=tree_request.position,
            status='pending'  # فقط قيد الانتظار
        ).order_by('position')
        
        for req in next_requests:
            req.position = req.position - 1
            req.save()
        
        messages.success(request, 'تم إلغاء الطلب بنجاح!')
        return redirect('/requests/')
    
    context = {'tree_request': tree_request}
    return render(request, 'core/cancel_request.html', context)

def tree_requests_list(request):
    pending_requests = TreeRequest.objects.filter(status='pending').order_by('position')
    completed_requests = TreeRequest.objects.filter(status='completed').order_by('-completed_date')
    cancelled_requests = TreeRequest.objects.filter(status='cancelled').order_by('-request_date')
    
    context = {
        'pending_requests': pending_requests,
        'completed_requests': completed_requests,
        'cancelled_requests': cancelled_requests,
    }
    return render(request, 'core/tree_requests_list.html', context)
def confirm_request(request, pk):
    tree_request = get_object_or_404(TreeRequest, pk=pk)
    
    # إذا كان الطلب مكتملاً بالفعل
    if tree_request.status == 'completed':
        messages.warning(request, 'هذا الطلب مكتمل بالفعل!')
        return redirect('/requests/')
    
    if request.method == 'POST':
        form = ConfirmRequestForm(request.POST)
        if form.is_valid():
            trees_provided = form.cleaned_data['trees_provided']
            notes = form.cleaned_data['notes']
            
            # تحديث حالة الطلب
            tree_request.status = 'completed'
            tree_request.completed_date = timezone.now()
            tree_request.notes = (tree_request.notes or '') + f'\nتم الإكمال: {notes}'
            tree_request.save()
            
            # إعادة ترتيب الأرقام للطلبات التالية
            next_requests = TreeRequest.objects.filter(
                position__gt=tree_request.position,
                status__in=['pending', 'in_progress']
            ).order_by('position')
            
            for req in next_requests:
                req.position = req.position - 1
                req.save()
            
            messages.success(request, 'تم تأكيد استلام الشجرة بنجاح!')
            return redirect('/requests/')
    else:
        # عرض النموذج مع القيمة الافتراضية
        form = ConfirmRequestForm(initial={'trees_provided': tree_request.quantity})
    
    context = {
        'tree_request': tree_request,
        'form': form,
    }
    return render(request, 'core/confirm_request.html', context)

def cancel_request(request, pk):
    tree_request = get_object_or_404(TreeRequest, pk=pk)
    if tree_request.status == 'completed':
        messages.warning(request, 'لا يمكن إلغاء طلب مكتمل!')
        return redirect('tree_requests_list')
    
    if request.method == 'POST':
        tree_request.status = 'cancelled'
        tree_request.save()
        
        next_requests = TreeRequest.objects.filter(
            position__gt=tree_request.position,
            status__in=['pending', 'in_progress']
        ).order_by('position')
        
        for req in next_requests:
            req.position = req.position - 1
            req.save()
        
        messages.success(request, 'تم إلغاء الطلب بنجاح!')
        return redirect('/requests/')
    
    context = {'tree_request': tree_request}
    return render(request, 'core/cancel_request.html', context)

def statistics(request):
    total_sales_weight = Sale.objects.aggregate(total=Sum('weight_kg'))['total'] or 0
    total_sales_value = Sale.objects.aggregate(total=Sum('total_price'))['total'] or 0
    
    # حساب إجمالي تكلفة الأشجار
    total_trees_cost = 0
    for sale in Sale.objects.all():
        total_trees_cost += sale.get_trees_total_cost()
    
    remaining_balance = total_sales_value - total_trees_cost
    
    total_participants = Participant.objects.filter(is_active=True).count()
    participants_with_requests = Participant.objects.filter(
        treerequest__isnull=False
    ).distinct().count()
    total_trees_requested = TreeRequest.objects.filter(
        status='completed'
    ).aggregate(total=Sum('quantity'))['total'] or 0
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
    
    context = {
        'total_sales_weight': total_sales_weight,
        'total_sales_value': total_sales_value,
        'total_trees_cost': total_trees_cost,
        'remaining_balance': remaining_balance,
        'total_participants': total_participants,
        'participants_with_requests': participants_with_requests,
        'total_trees_requested': total_trees_requested,
        'top_participants': top_participants,
        'tree_distribution': tree_distribution,
        'monthly_sales': monthly_sales,
    }
    return render(request, 'core/statistics.html', context)