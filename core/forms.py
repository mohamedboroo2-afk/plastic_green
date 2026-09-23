from django import forms
from django.core.exceptions import ValidationError
from .models import Sale, Participant, Tree, TreeRequest, SaleTree, SaleExpense, ExpenseCategory
from django.forms import inlineformset_factory


class SaleForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = ['sale_date', 'weight_kg', 'price_per_kg', 'notes']
        widgets = {
            'sale_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'weight_kg': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'price_per_kg': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean_weight_kg(self):
        weight = self.cleaned_data.get('weight_kg')
        if weight <= 0:
            raise ValidationError("الوزن يجب أن يكون أكبر من صفر")
        return weight


class SaleTreeForm(forms.ModelForm):
    class Meta:
        model = SaleTree
        fields = ['tree', 'quantity', 'price_per_tree']
        widgets = {
            'tree': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'price_per_tree': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }


class SaleExpenseForm(forms.ModelForm):
    class Meta:
        model = SaleExpense
        fields = ['category', 'quantity', 'price_per_unit', 'description']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'price_per_unit': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ملاحظة اختيارية'}),
        }


SaleTreeFormSet = inlineformset_factory(
    Sale,
    SaleTree,
    form=SaleTreeForm,
    extra=2,
    can_delete=True
)

SaleExpenseFormSet = inlineformset_factory(
    Sale,
    SaleExpense,
    form=SaleExpenseForm,
    extra=2,
    can_delete=True
)


class ParticipantForm(forms.ModelForm):
    class Meta:
        model = Participant
        fields = ['name', 'phone', 'address']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'الاسم الكامل'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'اختياري - اتركه فارغاً إذا لم يوجد'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'العنوان (اختياري)'}),
        }


class TreeForm(forms.ModelForm):
    class Meta:
        model = Tree
        fields = ['tree_type', 'description']
        widgets = {
            'tree_type': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'مثال: تمر، رمان، مانجو، إلخ'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'وصف اختياري'}),
        }


class ExpenseCategoryForm(forms.ModelForm):
    class Meta:
        model = ExpenseCategory
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'مثال: أصيص، أكياس قمامة، بنزين، نقل'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'وصف اختياري'}),
        }


class TreeRequestForm(forms.ModelForm):
    class Meta:
        model = TreeRequest
        fields = ['participant', 'tree', 'quantity', 'notes']
        widgets = {
            'participant': forms.Select(attrs={'class': 'form-control select2-participant'}),
            'tree': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['participant'].queryset = Participant.objects.filter(is_active=True).order_by('name')
        self.fields['participant'].label = "المشارك (ابحث بالاسم أو رقم الموبايل)"


class ConfirmRequestForm(forms.Form):
    trees_provided = forms.IntegerField(
        min_value=1,
        label="عدد الأشجار المقدمة",
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        label="ملاحظات الإكمال"
    )