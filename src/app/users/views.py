from django.shortcuts import render, redirect

from django.contrib.auth.models import Group

from .forms import UserCreationForm


def register(request):
    form = UserCreationForm(request.POST or None)
    if form.is_valid():
        user = form.save()  # Group add should save user first.
        user.is_staff = True  # Can login to admin site.
        user.groups.add(Group.objects.get(name='teacher'))
        user.save()
        return redirect('admin:index')

    return render(request, 'register.html', {'form': form})
