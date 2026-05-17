from django.db import models


class Users(models.Model):
    email = models.EmailField(unique=True)
    fullName = models.CharField(max_length=120)
    password_hash = models.CharField(max_length=255)

    def __str__(self):
        return self.email


class Company(models.Model):
    companyId = models.CharField(unique=True, max_length=100)
    cName = models.CharField(max_length=200)
    user = models.ForeignKey(
        Users,
        on_delete=models.CASCADE,
        related_name="companies"
    )

    def __str__(self):
        return self.cName


class AccountingRecord(models.Model):
    RECORD_TYPES = [
        ("gelir", "Gelir"),
        ("gider", "Gider"),
    ]

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="accounting_records"
    )
    record_type = models.CharField(max_length=10, choices=RECORD_TYPES)
    date = models.DateField(null=True, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    description = models.TextField(null=True, blank=True)

    # Dosya kaydedilmez. Sadece bu kaydın dosyadan/görüntü işlemeden geldiğini belirtir.
    created_from_file = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.company.cName} - {self.record_type} - {self.amount or '-'}"


class CompanyMonthly(models.Model):
    income = models.FloatField()
    expenditure = models.FloatField()
    result = models.FloatField()
    month = models.CharField(max_length=20)
    company = models.OneToOneField(
        Company,
        on_delete=models.CASCADE,
    )


class CompanyDaily(models.Model):
    income = models.FloatField()
    expenditure = models.FloatField()
    result = models.FloatField()
    day = models.CharField(max_length=20)
    company = models.OneToOneField(
        Company,
        on_delete=models.CASCADE,
    )
