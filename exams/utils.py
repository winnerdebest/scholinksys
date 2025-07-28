from django.shortcuts import redirect

def exam_session_required(view_func):
    def wrapper(request, *args, **kwargs):
        if request.session.get('exam_logged_in') != True:
            return redirect('exam_login')
        return view_func(request, *args, **kwargs)
    return wrapper
