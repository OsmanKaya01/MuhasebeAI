from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="homepage"),
    path("dashboard", views.dashboard, name="dashboard"),
    path("add-company", views.addCompany, name="addCompany"),
    path("delete-company", views.deleteCompany, name="deleteCompany"),
    path("muhasebe/gecici-ekle", views.addTempAccountingRecord, name="addTempAccountingRecord"),
    path("muhasebe/gecici-sil/<str:record_id>", views.deleteTempAccountingRecord, name="deleteTempAccountingRecord"),
    path("muhasebe/kaydet", views.savePendingAccountingRecords, name="savePendingAccountingRecords"),
    path("muhasebe/temizle", views.clearCompanyTable, name="clearCompanyTable"),
    path("gunluk-rapor/satir-sil/<int:company_id>/<str:date_label>/",views.delete_daily_report_row,name="delete_daily_report_row"),
]
