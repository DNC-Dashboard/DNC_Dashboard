from django.shortcuts import render
from django.contrib.auth.decorators import login_required


from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect

def register(request):
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')  # go to login after successful signup
    else:
        form = UserCreationForm()

    return render(request, 'accounts/register.html', {'form': form})






@login_required(login_url='/login/')
def index(request):
    return render(request, 'pages/index.html')

@login_required(login_url='/login/')
def members(request):
    return render(request, 'pages/members.html')

# Analytics
@login_required(login_url='/login/')
def analytics(request):
    return render(request, "pages/analytics.html")

@login_required(login_url='/login/')
def task_management(request):
    return render(request, "pages/kanban.html")

@login_required(login_url='/login/')
def projects(request):
    return render(request, "pages/projects.html")

@login_required(login_url='/login/')
def campaigns(request):
    return render(request, "pages/campaigns.html")

# Profile (this fixes the {% url 'profile' %} error)
@login_required(login_url='/login/')
def profile(request):
    return render(request, "pages/profile.html")

@login_required(login_url='/login/')
def configuration(request):
    return render(request, "pages/configuration.html")

@login_required(login_url='/login/')
def assets(request):
    return render(request, "pages/assets.html")
