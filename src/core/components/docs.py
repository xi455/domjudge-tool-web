SWAGGER_SETTINGS = {
    "DEFAULT_INFO": "core.docs.info",
    "USE_SESSION_AUTH": False,
    "SECURITY_DEFINITIONS": {
        "Token": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "Format: `token {token}`",
        },
    },
}
