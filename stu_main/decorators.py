from django.http import HttpResponseForbidden
from functools import wraps

def student_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.user_type == 'student':
            return view_func(request, *args, **kwargs)
        return HttpResponseForbidden("Access denied. Students only.")
    return _wrapped_view
