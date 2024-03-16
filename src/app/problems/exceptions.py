class ProblemException(Exception):
    pass

class ProblemCreateLogException(ProblemException):
    pass

class ProblemDownloaderException(Exception):
    pass


class ProblemDownloaderLoginException(ProblemDownloaderException):
    pass


class ProblemDownloaderDownloadFailException(ProblemDownloaderException):
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