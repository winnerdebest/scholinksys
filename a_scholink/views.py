from django.shortcuts import render

def universal_error_view(request, exception=None):
    return render(request, 'errors/404.html', status=404)



def internal_server_error_view(request):
    return render(request, 'errors/404.html', status=500)