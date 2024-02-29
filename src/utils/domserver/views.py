from app.users.models import User

def create_contest_record(request, form, client_obj, problem_crawler):
    """
    Create a contest.

    Args:
        request: The HTTP request object.
        form: The form object containing the contest data.
        client_obj: The client object representing the server.
        problem_crawler: The problem crawler object.

    Returns:
        None
    """
    form.instance.owner = User.objects.get(username=request.user.username)
    form.instance.server_client = client_obj
    form.instance.cid = problem_crawler.get_contest_name_cid(contest_shortname=form.instance.short_name)
    form.save()