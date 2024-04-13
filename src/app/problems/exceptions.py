class ProblemDownloaderException(Exception):
    pass


class ProblemDownloaderLoginException(ProblemDownloaderException):
    pass


class ProblemDownloaderDownloadFailException(ProblemDownloaderException):
    pass


class ProblemDownloaderDemoContestNotFoundException(ProblemDownloaderException):
    pass


class ProblemCreateLogException(Exception):
    pass


class ProblemUploadException(Exception):
    pass


class ProblemUnZipException(Exception):
    pass


class ProblemUnZipUploadRequiredFileException(ProblemUnZipException):
    pass


class ProblemUnZipInOutFormatException(ProblemUnZipException):
    pass


class ProblemUnZipInOutCreateException(ProblemUnZipException):
    pass


class ProblemUnZipCreateException(ProblemUnZipException):
    pass


class ProblemReplaceException(Exception):
    pass


class ProblemReplaceUploadException(Exception):
    pass


class ProblemReplaceUpdateLogException(ProblemReplaceException):
    pass


class ProblemTestCaseException(Exception):
    pass


class ProblemTestCaseUploadException(ProblemTestCaseException):
    pass