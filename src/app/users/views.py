from django.contrib.auth import forms
from django.shortcuts import render, redirect

from django.contrib.auth.models import Group

from .models import User


class UserCreationForm(forms.UserCreationForm):
    class Meta(forms.UserCreationForm.Meta):
        model = User


def register(request):
    form = UserCreationForm(request.POST or None)
    if form.is_valid():
        user = form.save()  # Group add should save user first.
        user.is_staff = True
        user.groups.add(Group.objects.get(name='teacher'))
        user.save()
        return redirect('admin:index')

    return render(request, 'register.html', {'form': form})
