from cn_s3_api.utils import parse_list

COLD_ARCHIVE_METHOD = 'OVH_ARCHIVE'
COLD_RESTORE_METHOD = 'OVH_RESTORE'


class S3ColdBucket(object):
    def __init__(self, s3_client):
        self._s3_client = s3_client

    def list(self, bucket: str, _id, prefix=None) -> [dict]:
        return parse_list(self._s3_client.list_objects(Bucket=bucket, Prefix=prefix if prefix else '')['Contents'])

    def status(self, bucket, _id, prefix=None):
        return self._s3_client.get_bucket_intelligent_tiering_configuration(
            Bucket=bucket,
            Id=_id
        )

    def delete(self, bucket, _id, prefix=None):
        return self._s3_client.delete_bucket_intelligent_tiering_configuration(
            Bucket=bucket,
            Id=_id
        )

    def archive(self, bucket, _id, prefix=None):
        return self._set_bucket_rule(COLD_ARCHIVE_METHOD, bucket, _id)

    def restore(self, bucket, _id, prefix=None):
        return self._set_bucket_rule(COLD_RESTORE_METHOD, bucket, _id)

    def _set_bucket_rule(self, action, bucket, _id):
        return self._s3_client.put_bucket_intelligent_tiering_configuration(
            Bucket=bucket,
            Id=_id,
            IntelligentTieringConfiguration={
                "Id": _id,
                "Status": "Enabled",
                "Tierings": [{
                    "Days": 999,
                    "AccessTier": action
                }]
            }
        )
