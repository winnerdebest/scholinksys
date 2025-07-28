from django.http import HttpResponseForbidden
from functools import wraps

def role_required(*allowed_roles):
    """
    Allows access only to users with specified `user_type` roles.
    Usage: @role_required('student', 'principal')
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_authenticated and request.user.user_type in allowed_roles:
                return view_func(request, *args, **kwargs)
            return HttpResponseForbidden("Access denied.")
        return _wrapped_view
    return decorator
