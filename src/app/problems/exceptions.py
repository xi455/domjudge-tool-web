class ProblemDownloaderException(Exception):
    pass


class ProblemDownloaderLoginException(ProblemDownloaderException):
    pass


class ProblemDownloaderDownloadFailException(ProblemDownloaderException):
    pass


class ProblemUnZipException(Exception):
    pass