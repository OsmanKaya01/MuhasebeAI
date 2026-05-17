from functools import wraps
from django.shortcuts import redirect
from users.models import Users

SESSION_KEY = "user_id"

def get_current_user(request):
    uid = request.session.get(SESSION_KEY)
    if not uid:
        return None
    try:
        return Users.objects.get(id=uid)
    except Users.DoesNotExist:
        return None

def login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get(SESSION_KEY):
            return redirect("/auth/login")
        return view_func(request, *args, **kwargs)
    return wrapper
