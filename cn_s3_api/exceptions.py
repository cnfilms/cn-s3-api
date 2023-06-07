class S3Error(Exception):
    pass


class S3UploadError(S3Error):
    pass


class S3BucketError(S3Error):
    pass


class S3BucketMethodNotImplemented(S3Error):
    pass


class S3BucketInvalidParameter(S3Error):
    pass
