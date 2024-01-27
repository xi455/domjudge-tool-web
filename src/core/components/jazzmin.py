JAZZMIN_SETTINGS: dict = {
    # title of the window (Will default to current_admin_site.site_title if absent or None)  # noqa: E501
    "site_title": "judge-tool",
    # Title on the brand, and login screen (19 chars max) (defaults to current_admin_site.site_header if absent or
    # None)  # noqa: E501
    "site_header": "Judge Tool",
    # square logo to use for your site, must be present in static files, used for favicon and brand on top left  #
    # noqa: E501
    # 'site_logo': 'problems/img/logo.png',
    # Welcome text on the login screen
    "welcome_sign": "歡迎使用 Judge Tool",
    # Copyright on the footer
    "copyright": "NTUB",
    # The model admin to search from the search bar, search bar omitted if excluded  # noqa: E501
    "search_model": "users.User",
    # Field name on user model that contains avatar image
    "user_avatar": None,
    ############
    # Top Menu #
    ############
    # Links to put along the top menu
    "topmenu_links": [
        # Url that gets reversed (Permissions can be added)
        {
            "name": "Home",
            "url": "admin:index",
            "permissions": ["users.view_user"],
        },
        # external url that opens in a new window (Permissions can be added)
        # {
        #     'name': 'Support',
        #     'url': 'https://github.com/farridav/django-jazzmin/issues',
        #     'new_window': True
        # },
        # model admin to link to (Permissions checked against model)
        # App with dropdown menu to all its models pages (Permissions checked against models)  # noqa: E501
        {
            "app": "problems",
        },
        {
            "name": "API 文件",
            "url": "api:docs",
            "permissions": ["users.view_user"],
            "new_window": True,
        },
    ],
    #############
    # User Menu #
    #############
    # Additional links to include in the user menu on the top right ('app' url type is not allowed)  # noqa: E501
    "usermenu_links": [
        # {
        #     'name': 'Support',
        #     'url': 'https://github.com/farridav/django-jazzmin/issues',
        #     'new_window': True
        # },
        {
            "model": "users.user",
        },
    ],
    #############
    # Side Menu #
    #############
    # Whether to display the side menu
    "show_sidebar": True,
    # Whether to aut expand the menu
    "navigation_expanded": True,
    # Hide these apps when generating side menu e.g (auth)
    "hide_apps": [],
    # Hide these models when generating side menu (e.g auth.user)
    "hide_models": [],
    # List of apps (and/or models) to base side menu ordering off of (does not need to contain all apps/models)  #
    # noqa: E501
    "order_with_respect_to": [
        "auth",
        "users",
        "problems",
        "problems.Problem",
    ],
    # Custom links to append to app groups, keyed on app name
    # 'custom_links': {
    #     'apis': [{
    #         "name": "API 文件",
    #         "url": "api:docs",
    #         "permissions": ["users.view_user"],
    #         "new_window": True
    #     },]
    # },
    # Custom icons for side menu apps/models See https://fontawesome.com/icons?d=gallery&m=free  # noqa: E501
    # for a list of icon classes
    "icons": {
        "auth": "fas fa-users-cog",
        "users": "fas fa-users-cog",
        "users.user": "fas fa-user",
        "auth.Group": "fas fa-users",
        "problems.Problem": "fas fa-file-import",
        "authtoken.TokenProxy": "fas fa-key",
    },
    # Icons that are used when one is not manually specified
    "default_icon_parents": "fas fa-chevron-circle-right",
    "default_icon_children": "fas fa-circle",
    #################
    # Related Modal #
    #################
    # Use modals instead of popups
    "related_modal_active": False,
    #############
    # UI Tweaks #
    #############
    # Relative paths to custom CSS/JS scripts (must be present in static files)
    "custom_css": "jazzmin.css",
    "custom_js": None,
    # Whether to show the UI customizer on the sidebar
    "show_ui_builder": False,
    ###############
    # Change view #
    ###############
    # Render out the change view as a single form, or in tabs, current options are  # noqa: E501
    # - single
    # - horizontal_tabs (default)
    # - vertical_tabs
    # - collapsible
    # - carousel
    "changeform_format": "horizontal_tabs",
    # override change forms on a per modeladmin basis
    "changeform_format_overrides": {
        "users.user": "collapsible",
        "auth.group": "vertical_tabs",
    },
    # Add a language dropdown into the admin
    "language_chooser": False,
}
