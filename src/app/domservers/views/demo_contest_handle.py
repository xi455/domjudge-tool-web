from app.domservers.models.dom_server import DomServerContest

def demo_contest_data(admin_owner, server_client):
    demo_contest = DomServerContest(
        owner=admin_owner,
        server_client=server_client,
        cid=None,
        name="Demo contest",
        short_name="demo",
        start_time="2024-01-01 13:00:00 Asia/Taipei",
        end_time="2024-01-01 18:00:00 Asia/Taipei",
        activate_time="2024-01-01 12:00:00 Asia/Taipei",
        scoreboard_freeze_length="",
        scoreboard_unfreeze_time="",
        deactivate_time="",
        start_time_enabled=False,
        process_balloons=False,
        open_to_all_teams=False,
        contest_visible_on_public_scoreboard=False,
        enabled=False,
    )

    return demo_contest


def upload_demo_contest(problem_crawler, admin_owner, server_client):
    demo_contest_response = demo_contest_data(admin_owner, server_client)
    create_response = problem_crawler.contest_format_process(
            contest_data=demo_contest_response
        )

    result = problem_crawler.contest_and_problem_create(
        create_contest_information=create_response
    )

    return result, demo_contest_response