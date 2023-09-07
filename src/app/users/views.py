from django.contrib.auth.models import Group
from django.shortcuts import redirect, render

from .forms import UserCreationForm


def register(request):
    form = UserCreationForm(request.POST or None)
    if form.is_valid():
        user = form.save()  # Group add should save user first.
        user.is_staff = True  # Can login to admin site.
        teacher_group, _ = Group.objects.get_or_create(name="teacher")
        user.groups.add(teacher_group)
        user.save()
        return redirect("admin:index")

    return render(request, "register.html", {"form": form})
