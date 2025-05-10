from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required


def homepage(request):
    return render(request , "homepage.html", {})

def authView(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST or None)
        if form.is_valid():
            form.save()
            return redirect("shared:login")
    else:
        form = UserCreationForm()
    return render(request, "registration/register.html", {"form" :form})