from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone


class Participant(models.Model):
    """نموذج المشاركين المتعاونين"""
    name = models.CharField(max_length=200, verbose_name="الاسم")
    phone = models.CharField(max_length=15, blank=True, null=True, verbose_name="رقم الموبايل")  # أصبح اختيارياً
    address = models.TextField(blank=True, null=True, verbose_name="العنوان")
    join_date = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الانضمام")
    is_active = models.BooleanField(default=True, verbose_name="نشط")

    class Meta:
        verbose_name = "مشارك"
        verbose_name_plural = "المشاركون"
        ordering = ['-join_date']

    def __str__(self):
        return f"{self.name} - {self.phone}" if self.phone else self.name

    def get_total_plastic_weight(self):
        return self.sale_set.aggregate(
            total=models.Sum('weight_kg')
        )['total'] or 0

    def get_completed_requests_count(self):
        return self.treerequest_set.filter(status='completed').count()


class Tree(models.Model):
    """نموذج أنواع الأشجار"""
    tree_type = models.CharField(
        max_length=50,
        verbose_name="نوع الشجرة",
        unique=True
    )
    description = models.TextField(blank=True, null=True, verbose_name="وصف")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "شجرة"
        verbose_name_plural = "الأشجار"
        ordering = ['tree_type']

    def __str__(self):
        return self.tree_type


class ExpenseCategory(models.Model):
    """نموذج أنواع المصروفات"""
    name = models.CharField(max_length=100, verbose_name="اسم المصروف", unique=True)
    description = models.TextField(blank=True, null=True, verbose_name="وصف")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "نوع مصروف"
        verbose_name_plural = "أنواع المصروفات"
        ordering = ['name']

    def __str__(self):
        return self.name


class Sale(models.Model):
    """نموذج عمليات البيع"""
    sale_date = models.DateField(default=timezone.now, verbose_name="تاريخ البيع")
    weight_kg = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        verbose_name="الوزن بالكيلو"
    )
    price_per_kg = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=2.50,
        verbose_name="سعر الكيلو"
    )
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        editable=False,
        verbose_name="إجمالي المبيعات"
    )
    participant = models.ForeignKey(
        Participant,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="المشارك"
    )
    trees_purchased = models.ManyToManyField(
        Tree,
        through='SaleTree',
        verbose_name="الأشجار المشتراة"
    )
    notes = models.TextField(blank=True, null=True, verbose_name="ملاحظات")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "بيع"
        verbose_name_plural = "المبيعات"
        ordering = ['-sale_date']

    def save(self, *args, **kwargs):
        self.total_price = self.weight_kg * self.price_per_kg
        super().save(*args, **kwargs)

    def get_trees_total_cost(self):
        """إجمالي تكلفة الأشجار المشتراة"""
        total = 0
        for st in self.saletree_set.all():
            total += st.quantity * st.price_per_tree
        return total

    def get_expenses_total_cost(self):
        """إجمالي تكلفة المصروفات الأخرى"""
        total = 0
        for exp in self.saleexpense_set.all():
            total += exp.quantity * exp.price_per_unit
        return total

    def get_all_expenses(self):
        """إجمالي كل المصروفات (أشجار + أخرى)"""
        return self.get_trees_total_cost() + self.get_expenses_total_cost()

    def get_remaining_amount(self):
        """المبلغ المتبقي بعد كل المصروفات"""
        return self.total_price - self.get_all_expenses()

    def __str__(self):
        return f"{self.sale_date} - {self.weight_kg} كجم - {self.total_price} د.ل"


class SaleTree(models.Model):
    """نموذج وسيط بين البيع والأشجار - مع سعر كل شجرة"""
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE)
    tree = models.ForeignKey(Tree, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1, verbose_name="العدد")
    price_per_tree = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="سعر الشجرة"
    )

    class Meta:
        verbose_name = "شجرة في البيع"
        verbose_name_plural = "الأشجار في البيع"

    def get_total_price(self):
        return self.quantity * self.price_per_tree

    def __str__(self):
        return f"{self.sale} - {self.tree} × {self.quantity} - {self.price_per_tree} د.ل"


class SaleExpense(models.Model):
    """نموذج مصروفات البيع (أصيص، أكياس، بنزين، نقل، إلخ)"""
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE)
    category = models.ForeignKey(ExpenseCategory, on_delete=models.CASCADE, verbose_name="نوع المصروف")
    quantity = models.PositiveIntegerField(default=1, verbose_name="العدد")
    price_per_unit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="سعر الوحدة"
    )
    description = models.CharField(max_length=255, blank=True, null=True, verbose_name="ملاحظة")

    class Meta:
        verbose_name = "مصروف بيع"
        verbose_name_plural = "مصروفات البيع"

    def get_total_price(self):
        return self.quantity * self.price_per_unit

    def __str__(self):
        return f"{self.category} × {self.quantity} - {self.price_per_unit} د.ل"


class TreeRequest(models.Model):
    """نموذج طلبات الأشجار"""
    STATUS_CHOICES = [
        ('pending', 'قيد الانتظار'),
        ('completed', 'مكتمل'),
        ('cancelled', 'ملغي'),
    ]

    participant = models.ForeignKey(
        Participant,
        on_delete=models.CASCADE,
        verbose_name="المشارك"
    )
    tree = models.ForeignKey(
        Tree,
        on_delete=models.CASCADE,
        verbose_name="نوع الشجرة"
    )
    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="العدد"
    )
    request_date = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الطلب")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="الحالة"
    )
    position = models.PositiveIntegerField(
        editable=False,
        null=True,
        blank=True,
        verbose_name="رقم الدور"
    )
    notes = models.TextField(blank=True, null=True, verbose_name="ملاحظات")
    completed_date = models.DateTimeField(null=True, blank=True, verbose_name="تاريخ الإكمال")

    class Meta:
        verbose_name = "طلب شجرة"
        verbose_name_plural = "طلبات الأشجار"
        ordering = ['position', 'request_date']

    def save(self, *args, **kwargs):
        if not self.position:
            last_request = TreeRequest.objects.filter(
                status='pending'
            ).order_by('-position').first()
            self.position = (last_request.position + 1) if last_request else 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.participant.name} - {self.tree} × {self.quantity} - {self.get_status_display()}"