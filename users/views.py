from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Users,Company
from .security import hash_password, verify_password
from .auth import SESSION_KEY

def register_view(request):
    if request.method == "POST":
        email = (request.POST.get("email") or "").strip().lower()
        full_name = (request.POST.get("fullName") or "").strip()
        password1 = request.POST.get("password1") or ""
        password2 = request.POST.get("password2") or ""

        if not email or not full_name or not password1:
            messages.error(request, "Tüm alanları doldur.")
            return render(request, "users/sign.html")

        if password1 != password2:
            messages.error(request, "Şifreler aynı değil.")
            return render(request, "users/sign.html")

        if Users.objects.filter(email=email).exists():
            messages.error(request, "Bu e-posta zaten kayıtlı.")
            return render(request, "users/sign.html")

        user = Users.objects.create(
            email=email,
            fullName=full_name,
            password_hash=hash_password(password1),
        )

        # kayıt sonrası otomatik giriş
        request.session[SESSION_KEY] = user.id
        return redirect("dashboard")

    return render(request, "users/sign.html")


def login_view(request):
    if request.method == "POST":
        email = (request.POST.get("email") or "").strip().lower()
        password = request.POST.get("password") or ""

        user = Users.objects.filter(email=email).first()
        if not user or not verify_password(password, user.password_hash):
            print("çalışmadı")
            messages.error(request, "E-posta veya şifre yanlış.")
            return render(request, "users/login.html")

        request.session[SESSION_KEY] = user.id
        return redirect("dashboard")

    return render(request, "users/login.html")


def logout_view(request):
    request.session.flush()
    return redirect("homepage")


def create_company(request):
    if request.method == "POST":
        cName = (request.POST.get("cName") or "").strip().lower()
        companyId = (request.POST.get("companyId") or "").strip()

        if not companyId or not cName:
            messages.error(request, "Tüm alanları doldur.")
            return render(request, "users/companyCreate.html")

        if Company.objects.filter(companyId=companyId).exists():
            messages.error(request, "Bu şirket ID zaten kayıtlı.")
            return render(request, "users/companyCreate.html")

        Company.objects.create(
            companyId=companyId,
            cName=cName,
        )
        
        return redirect("/dashboard")
    
    return redirect("/auth/create-company")

