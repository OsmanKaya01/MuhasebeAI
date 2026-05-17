from decimal import Decimal, InvalidOperation
import uuid

from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from users.auth import get_current_user, login_required
from users.models import AccountingRecord, Company
from users.security import verify_password

import json
from google import genai
from google.genai import types
import re
from datetime import datetime

import os
from dotenv import load_dotenv

load_dotenv()


PENDING_SESSION_KEY = "pending_accounting_records"
ACTIVE_COMPANY_SESSION_KEY = "active_company_id"
HIDDEN_TABLE_RECORDS_SESSION_KEY = "hidden_table_record_ids"


def home(request):
    return render(request, "pages/homepage.html")

def turkce_tarihi_duzenle(date_text):
    if not date_text:
        return ""

    aylar = {
        "ocak": "01",
        "şubat": "02",
        "subat": "02",
        "mart": "03",
        "nisan": "04",
        "mayıs": "05",
        "mayis": "05",
        "haziran": "06",
        "temmuz": "07",
        "ağustos": "08",
        "agustos": "08",
        "eylül": "09",
        "eylul": "09",
        "ekim": "10",
        "kasım": "11",
        "kasim": "11",
        "aralık": "12",
        "aralik": "12",
    }

    date_text = date_text.strip().lower()

    # Zaten 2024-05-11 şeklindeyse aynen döndür
    try:
        tarih = datetime.strptime(date_text, "%Y-%m-%d")
        return tarih.strftime("%Y-%m-%d")
    except ValueError:
        pass

    # 11-05-2024 şeklindeyse 2024-05-11 yap
    try:
        tarih = datetime.strptime(date_text, "%d-%m-%Y")
        return tarih.strftime("%Y-%m-%d")
    except ValueError:
        pass

    # 11/05/2024 şeklindeyse 2024-05-11 yap
    try:
        tarih = datetime.strptime(date_text, "%d/%m/%Y")
        return tarih.strftime("%Y-%m-%d")
    except ValueError:
        pass

    # 11 Mayıs 2024 şeklindeyse 2024-05-11 yap
    parcalar = date_text.split()

    if len(parcalar) == 3:
        gun = parcalar[0].zfill(2)
        ay_adi = parcalar[1]
        yil = parcalar[2]

        ay = aylar.get(ay_adi)

        if ay:
            return f"{yil}-{ay}-{gun}"

    return ""

def parse_gemini_json(text):
    text = text.strip()

    # Gemini cevabı ```json ... ``` şeklinde geldiyse temizle
    text = text.replace("```json", "")
    text = text.replace("```", "")
    text = text.strip()

    # Yine de içinde ekstra yazı varsa sadece { ... } kısmını al
    match = re.search(r"\{.*\}", text, re.DOTALL)

    if match:
        text = match.group(0)

    return json.loads(text)


def process_receipt_file(uploaded_file, record_type):
    client = genai.Client(api_key= os.getenv("API_KEY"))

    file_bytes = uploaded_file.read()
    mime_type = uploaded_file.content_type

    prompt = f"""
Bu dosya bir muhasebe kaydı için yüklendi.

Kayıt türü: {record_type}

Dosyadan şu bilgileri çıkar:
- date
- amount
- description

Sadece JSON döndür.

Format:
{{
  "date": "YYYY-MM-DD",
  "amount": "0.00",
  "description": "kısa açıklama"
}}
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            types.Part.from_bytes(
                data=file_bytes,
                mime_type=mime_type,
            ),
            prompt,
        ],
    )

    text = response.text.strip()

    try:
        result = parse_gemini_json(text)
    except json.JSONDecodeError:
        result = {
            "date": "",
            "amount": "",
            "description": "Gemini cevabı okunamadı.",
        }

    return {
        "date": turkce_tarihi_duzenle(result.get("date", "")),
        "amount": result.get("amount", ""),
        "description": result.get("description", ""),
    }


def _safe_decimal(value):
    if value in [None, "", "-"]:
        return None

    try:
        return Decimal(str(value).replace(",", "."))
    except (InvalidOperation, ValueError):
        return None


def _money_to_float(value):
    decimal_value = _safe_decimal(value)
    if decimal_value is None:
        return 0.0
    return float(decimal_value)


def _format_money(value):
    return f"{value:.2f}"


def _build_report_rows(rows):
    report_rows = []

    for row in rows:
        amount = _safe_decimal(row.get("amount"))
        if amount is None:
            continue

        date_value = row.get("date")
        if not date_value or date_value == "-":
            continue

        report_rows.append({
            "date": str(date_value),
            "amount": amount,
            "description": row.get("description") or "-",
            "is_temp": bool(row.get("is_temp")),
        })

    return report_rows

@login_required
@require_POST
def delete_daily_report_row(request, company_id, date_label):
    user = get_current_user(request)

    company = get_object_or_404(
        Company,
        id=company_id,
        user=user
    )

    AccountingRecord.objects.filter(
        company=company,
        date=date_label
    ).delete()

    request.session[ACTIVE_COMPANY_SESSION_KEY] = company.id
    request.session["open_report_after_redirect"] = "gunluk"
    request.session.modified = True

    messages.success(request, f"{date_label} tarihli günlük rapor kayıtları silindi.")
    return redirect("dashboard")


def _build_company_reports(company):
    # Raporlar tablo görünümünden bağımsızdır.
    # Temizle butonu sadece panel tablosunu gizler; raporlar veritabanındaki
    # gerçek AccountingRecord kayıtlarından hesaplanmaya devam eder.
    saved_records = AccountingRecord.objects.filter(company=company).order_by("-created_at", "-id")

    gelir_report_rows = []
    gider_report_rows = []

    for record in saved_records:
        if record.amount is None or not record.date:
            continue

        row = {
            "date": str(record.date),
            "amount": record.amount,
            "description": record.description or "-",
            "is_temp": False,
        }

        if record.record_type == "gelir":
            gelir_report_rows.append(row)
        elif record.record_type == "gider":
            gider_report_rows.append(row)

    total_income = sum((row["amount"] for row in gelir_report_rows), Decimal("0"))
    total_expense = sum((row["amount"] for row in gider_report_rows), Decimal("0"))
    net_result = total_income - total_expense

    daily_map = {}
    monthly_map = {}

    def add_to_maps(row, record_type):
        date_text = row["date"]
        month_text = date_text[:7] if len(date_text) >= 7 else date_text

        for data_map, key in [(daily_map, date_text), (monthly_map, month_text)]:
            if key not in data_map:
                data_map[key] = {
                    "label": key,
                    "income": Decimal("0"),
                    "expense": Decimal("0"),
                    "net": Decimal("0"),
                }

            if record_type == "gelir":
                data_map[key]["income"] += row["amount"]
            else:
                data_map[key]["expense"] += row["amount"]

            data_map[key]["net"] = data_map[key]["income"] - data_map[key]["expense"]

    for row in gelir_report_rows:
        add_to_maps(row, "gelir")

    for row in gider_report_rows:
        add_to_maps(row, "gider")

    company.report_summary = {
        "income": _format_money(float(total_income)),
        "expense": _format_money(float(total_expense)),
        "net": _format_money(float(net_result)),
        "is_profit": net_result >= 0,
    }

    company.daily_report_rows = sorted(daily_map.values(), key=lambda item: item["label"], reverse=True)
    company.monthly_report_rows = sorted(monthly_map.values(), key=lambda item: item["label"], reverse=True)

    for report_row in company.daily_report_rows + company.monthly_report_rows:
        report_row["income_display"] = _format_money(float(report_row["income"]))
        report_row["expense_display"] = _format_money(float(report_row["expense"]))
        report_row["net_display"] = _format_money(float(report_row["net"]))
        report_row["is_profit"] = report_row["net"] >= 0

def _get_pending_records(request):
    return request.session.get(PENDING_SESSION_KEY, {})


def _set_pending_records(request, pending_records):
    request.session[PENDING_SESSION_KEY] = pending_records
    request.session.modified = True


def _get_hidden_table_record_ids(request):
    return request.session.get(HIDDEN_TABLE_RECORDS_SESSION_KEY, {})


def _set_hidden_table_record_ids(request, hidden_record_ids):
    request.session[HIDDEN_TABLE_RECORDS_SESSION_KEY] = hidden_record_ids
    request.session.modified = True


def _build_table_rows(company, pending_records, hidden_record_ids=None):
    company_key = str(company.id)
    company_pending = pending_records.get(company_key, [])
    hidden_record_ids = hidden_record_ids or {}
    hidden_ids = hidden_record_ids.get(company_key, [])

    gelir_rows = []
    gider_rows = []

    for record in company_pending:
        row = {
            "id": record.get("id"),
            "is_temp": True,
            "date": record.get("date") or "-",
            "amount": record.get("amount") or "-",
            "description": record.get("description") or "-",
            "receipt_text": record.get("file_name") or "-",
        }

        if record.get("record_type") == "gelir":
            gelir_rows.append(row)
        elif record.get("record_type") == "gider":
            gider_rows.append(row)

    saved_records = (
        AccountingRecord.objects
        .filter(company=company)
        .exclude(id__in=hidden_ids)
        .order_by("-created_at", "-id")
    )

    for record in saved_records:
        row = {
            "id": record.id,
            "is_temp": False,
            "date": record.date or "-",
            "amount": record.amount if record.amount is not None else "-",
            "description": record.description or "-",
            "receipt_text": "Dosyadan işlendi" if record.created_from_file else "-",
        }

        if record.record_type == "gelir":
            gelir_rows.append(row)
        elif record.record_type == "gider":
            gider_rows.append(row)

    company.gelir_rows = gelir_rows
    company.gider_rows = gider_rows


@login_required
def dashboard(request):
    user = get_current_user(request)
    parts = user.fullName.split()
    companies = list(Company.objects.filter(user=user).order_by("id"))

    initials = ""
    for part in parts:
        initials += part[0].upper()

    pending_records = _get_pending_records(request)
    hidden_record_ids = _get_hidden_table_record_ids(request)

    for company in companies:
        _build_table_rows(company, pending_records, hidden_record_ids)
        _build_company_reports(company)

    active_company_id = request.session.get(ACTIVE_COMPANY_SESSION_KEY)

    if not active_company_id and companies:
        active_company_id = companies[0].id
    

    return render(
        request,
        "pages/dashboard.html",
        {
            "user": user,
            "avatar": initials,
            "companies": companies,
            "active_company_id": active_company_id,
        },
    )


@login_required
@require_POST
def addCompany(request):
    user = get_current_user(request)
    companyName = (request.POST.get("companyName") or "").strip()
    companyID = (request.POST.get("companyID") or "").strip()

    if not companyName or not companyID:
        messages.error(request, "Şirket ID ve şirket adı boş bırakılamaz.")
        return redirect("dashboard")

    if Company.objects.filter(companyId=companyID).exists():
        messages.error(request, "Bu şirket ID zaten kayıtlı.")
        return redirect("dashboard")

    company = Company.objects.create(
        cName=companyName,
        companyId=companyID,
        user=user,
    )

    request.session[ACTIVE_COMPANY_SESSION_KEY] = company.id
    return redirect("dashboard")


@login_required
@require_POST
def addTempAccountingRecord(request):
    user = get_current_user(request)

    company_id = request.POST.get("company_id")
    record_type = request.POST.get("record_type")

    company = get_object_or_404(Company, id=company_id, user=user)

    if record_type not in ["gelir", "gider"]:
        messages.error(request, "Geçersiz muhasebe kayıt türü.")
        return redirect("dashboard")

    date = (request.POST.get("date") or "").strip()
    amount = (request.POST.get("amount") or "").strip()
    description = (request.POST.get("description") or "").strip()
    receipt_file = request.FILES.get("receipt_file")

    manuel_bilgi_var = bool(date or amount or description)
    dosya_var = receipt_file is not None

    if not manuel_bilgi_var and not dosya_var:
        messages.error(request, "Lütfen manuel bilgi girin veya dosya yükleyin.")
        request.session[ACTIVE_COMPANY_SESSION_KEY] = company.id
        return redirect("dashboard")

    if manuel_bilgi_var and not (date and amount and description):
        messages.error(request, "Manuel girişte tarih, tutar ve açıklama birlikte doldurulmalı.")
        request.session[ACTIVE_COMPANY_SESSION_KEY] = company.id
        return redirect("dashboard")

    created_from_file = False
    file_name = ""

    if dosya_var:
        # Dosya burada kaydedilmez. Sadece görüntü işleme fonksiyonuna verilir.
        processed_data = process_receipt_file(receipt_file, record_type)
        created_from_file = True
        file_name = receipt_file.name

        # Görüntü işleme sonucu dolu gelirse manuel alanların yerine / boşsa yanına kullanılır.
        date = processed_data.get("date") or date
        amount = processed_data.get("amount") or amount
        description = processed_data.get("description") or description

    if amount and _safe_decimal(amount) is None:
        messages.error(request, "Tutar geçerli bir sayı olmalı.")
        request.session[ACTIVE_COMPANY_SESSION_KEY] = company.id
        return redirect("dashboard")

    pending_records = _get_pending_records(request)
    company_key = str(company.id)

    if company_key not in pending_records:
        pending_records[company_key] = []

    pending_records[company_key].append(
        {
            "id": str(uuid.uuid4()),
            "record_type": record_type,
            "date": date,
            "amount": amount,
            "description": description,
            "created_from_file": created_from_file,
            "file_name": file_name,
        }
    )

    _set_pending_records(request, pending_records)
    request.session[ACTIVE_COMPANY_SESSION_KEY] = company.id

    messages.success(request, "Kayıt tabloya eklendi. Veritabanına kaydetmek için Kaydet butonuna bas.")
    return redirect("dashboard")

@login_required
@require_POST
def deleteTempAccountingRecord(request, record_id):
    pending_records = _get_pending_records(request)

    for company_key, records in list(pending_records.items()):
        new_records = []

        for record in records:
            if record.get("id") == record_id:
                request.session[ACTIVE_COMPANY_SESSION_KEY] = int(company_key)
            else:
                new_records.append(record)

        pending_records[company_key] = new_records

    _set_pending_records(request, pending_records)
    messages.success(request, "Geçici kayıt tablodan silindi.")
    return redirect("dashboard")


@login_required
@require_POST
def savePendingAccountingRecords(request):
    user = get_current_user(request)
    company_id = request.POST.get("company_id")
    company = get_object_or_404(Company, id=company_id, user=user)

    pending_records = _get_pending_records(request)
    company_key = str(company.id)
    records = pending_records.get(company_key, [])

    if not records:
        messages.error(request, "Kaydedilecek geçici kayıt yok.")
        request.session[ACTIVE_COMPANY_SESSION_KEY] = company.id
        return redirect("dashboard")

    with transaction.atomic():
        for record in records:
            amount = _safe_decimal(record.get("amount"))

            AccountingRecord.objects.create(
                company=company,
                record_type=record.get("record_type"),
                date=record.get("date") or None,
                amount=amount,
                description=record.get("description") or None,
                created_from_file=bool(record.get("created_from_file")),
            )

    # Kayıtlar veritabanına aktarıldıktan sonra bu şirkete ait
    # geçici kayıtlar session içinden tamamen silinir.
    pending_records.pop(company_key, None)

    # Boş kalan şirket anahtarları varsa temizle.
    pending_records = {
        key: value
        for key, value in pending_records.items()
        if value
    }

    request.session[PENDING_SESSION_KEY] = pending_records
    request.session[ACTIVE_COMPANY_SESSION_KEY] = company.id
    request.session.modified = True

    messages.success(request, "Geçici kayıtlar veritabanına kaydedildi ve geçici liste temizlendi.")
    return redirect("dashboard")


@login_required
@require_POST
def clearCompanyTable(request):
    user = get_current_user(request)
    company_id = request.POST.get("company_id")
    company = get_object_or_404(Company, id=company_id, user=user)

    # Veritabanındaki kayıtlar silinmez. Sadece bu anki kayıtların id'leri
    # session içinde saklanır ve panel tablosunda gizlenir.
    saved_record_ids = list(
        AccountingRecord.objects.filter(company=company).values_list("id", flat=True)
    )

    hidden_record_ids = _get_hidden_table_record_ids(request)
    hidden_record_ids[str(company.id)] = saved_record_ids
    _set_hidden_table_record_ids(request, hidden_record_ids)

    # Geçici kayıtlar veritabanında olmadığı için panelden temizlenir.
    pending_records = _get_pending_records(request)
    pending_records.pop(str(company.id), None)
    _set_pending_records(request, pending_records)

    request.session[ACTIVE_COMPANY_SESSION_KEY] = company.id
    request.session.modified = True

    messages.success(request, "Panel tablosu temizlendi. Veritabanındaki kayıtlar silinmedi; raporlarda görünmeye devam eder.")
    return redirect("dashboard")


@login_required
@require_POST
def delete_daily_report_record(request, row_id):
    user = get_current_user(request)

    record = get_object_or_404(
        AccountingRecord,
        id=row_id,
        company__user=user
    )

    company_id = record.company.id

    record.delete()

    request.session["active_company_id"] = company_id
    request.session["open_report_after_redirect"] = "gunluk"
    request.session.modified = True

    messages.success(request, "Kayıt silindi.")
    return redirect("dashboard")

@login_required
@require_POST
def deleteCompany(request):
    user = get_current_user(request)
    company_id = request.POST.get("company_id")
    password = request.POST.get("password") or ""

    company = get_object_or_404(Company, id=company_id, user=user)

    if not verify_password(password, user.password_hash):
        messages.error(request, "Şifre hatalı. Şirket silinmedi.")
        request.session[ACTIVE_COMPANY_SESSION_KEY] = company.id
        return redirect("dashboard")

    pending_records = _get_pending_records(request)
    pending_records.pop(str(company.id), None)
    _set_pending_records(request, pending_records)

    hidden_record_ids = _get_hidden_table_record_ids(request)
    hidden_record_ids.pop(str(company.id), None)
    _set_hidden_table_record_ids(request, hidden_record_ids)

    company.delete()
    request.session.pop(ACTIVE_COMPANY_SESSION_KEY, None)

    messages.success(request, "Şirket ve kayıtları silindi.")
    return redirect("dashboard")
