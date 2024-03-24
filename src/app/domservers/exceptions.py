class ContestException(Exception):
    pass


class ContestCreateException(Exception):
    pass


class ContestCreateDuplicateException(ContestCreateException):
    pass


class ContestUpdateException(Exception):
    pass


class ContestCopyException(Exception):
    pass


class ContestCopyUploadException(ContestCopyException):
    pass


class ContestCopyShortNameException(ContestCopyException):
    pass


class ContestShortNameException(Exception):
    pass