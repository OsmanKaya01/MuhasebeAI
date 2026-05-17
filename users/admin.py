from django.contrib import admin
from .models import Users, Company, CompanyMonthly, CompanyDaily, AccountingRecord


@admin.register(Users)
class UsersAdmin(admin.ModelAdmin):
    list_display = ("id", "email", "fullName")
    search_fields = ("email", "fullName")


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("id", "companyId", "cName", "user")
    search_fields = ("companyId", "cName", "user__email")


@admin.register(AccountingRecord)
class AccountingRecordAdmin(admin.ModelAdmin):
    list_display = ("id", "company", "record_type", "date", "amount", "created_from_file", "created_at")
    list_filter = ("record_type", "created_from_file", "created_at")
    search_fields = ("company__cName", "description")


admin.site.register(CompanyMonthly)
admin.site.register(CompanyDaily)
