from django.shortcuts import render


# Create your views here.
def main_page(request):
    context = {}
    return render(request, 'main.html', context)


def lana_translate(request):
    return render(request, 'lana_translate.html')
