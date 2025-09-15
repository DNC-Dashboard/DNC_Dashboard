from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

# Create your views here.
@login_required(login_url='/login/')
def index(request):

    # Page from the theme 
    return render(request, 'pages/index.html')

@login_required(login_url='/login/')
def members(request):
    return render(request, 'pages/members.html')




# Create your views below 👇👇👇

# Analytics features
    
def analytics(request):
    return render(request, "pages/analytics.html")



    
def task_management(request):
    return render(request, "pages/task_management.html")



    