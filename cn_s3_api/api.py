import os
from bisect import bisect_left
from logging import getLogger
from pathlib import Path

import boto3

from cn_s3_api.cold import S3ColdBucket
from cn_s3_api.exceptions import S3BucketError, S3UploadError, S3BucketMethodNotImplemented
from cn_s3_api.progress import ProgressPercentage


class CNS3Api(object):
    def __init__(
            self,
            s3_config,
            progress=False,
            callback=None,
            logger_name=None
    ):
        self._s3_client = boto3.client('s3', **s3_config)
        self._s3_resource = boto3.resource('s3', **s3_config)
        self._s3_cold = S3ColdBucket(self._s3_client)

        self._exceptions = self._s3_client.exceptions
        self._callback = callback
        self._progress = ProgressPercentage if progress else None
        self._logger = getLogger(logger_name)

    def download(self, bucket_name, src, dst, skip_identical=True, extra_args=None):
        bucket = self._s3_resource.Bucket(bucket_name)
        dst = '{}{}'.format(dst, src)

        try:
            objects = [dict(name=f.key, size=f.size) for f in bucket.objects.filter(Prefix=src)]
        except self._exceptions.NoSuchBucket as e:
            self.notify({"success": False, "level": "folder"})
            raise S3BucketError(e)

        if len(objects) == 1:
            if self._download(bucket, src, dst, extra_args):
                self.notify(**{"success": True, "level": "file"})
            else:
                self.notify(**{"success": False, "level": "file"})

            return

        all_downloads_ok = True
        for obj in objects:
            target = os.path.join(dst, os.path.relpath(obj['name'], src))

            if not os.path.exists(os.path.dirname(target)):
                os.makedirs(os.path.dirname(target))

            if obj['name'][-1] == '/':
                continue

            if skip_identical and self._check_identical(obj, target):
                self._logger.info(f'S3: bucket: {bucket.name}, downloading: {target}: identical size, skipping..')
                self.notify({"success": True, "level": "file", "object": obj['name'], "action": "download_object"})
                continue

            if self._download(bucket, obj['name'], target, extra_args):
                self.notify({"success": True, "level": "file", "object": obj['name'], "action": "download_object"})
            else:
                self.notify({"success": False, "level": "file", "object": obj['name'], "action": "download_object"})
                all_downloads_ok = False

        self.notify({"success": all_downloads_ok, "level": "folder"})

    def _download(self, bucket, src, dst, extra_args=None):
        try:
            self._logger.info(f'S3: bucket: {bucket.name}, downloading: {src}...')
            bucket.download_file(
                src, dst, **extra_args, Callback=self._progress(src) if self._progress else None)
            self._logger.info(f'S3: bucket: {bucket.name}, downloading: {src} OK')
            return True
        except Exception as e:
            self._logger.info(f'S3: bucket: {bucket.name}, downloading: {src} NOK')
            return False

    def upload(self, bucket_name: str, source: str, prefix: str, extra_args=None) -> [str]:

        try:
            self._s3_client.create_bucket(Bucket=bucket_name)
            self._logger.info(f'S3: creating bucket: {bucket_name}')
        except (self._exceptions.BucketAlreadyOwnedByYou, self._exceptions.BucketAlreadyExists):
            self._logger.info(f'S3: bucket already exist: {bucket_name}')

        paths = self.list_source_objects(source_folder=source)

        objects = self.list(bucket_name, prefix)
        object_keys = [obj['Key'] for obj in objects]
        object_keys.sort()
        object_keys_length = len(object_keys)

        for path in paths:
            index = bisect_left(object_keys, path)
            if index == object_keys_length:
                src = str(Path(source).joinpath(path))
                dst = str(Path(prefix).joinpath(path))

                if self._upload(bucket_name, src, dst, extra_args):
                    self.notify({"success": "ok", "level": "file", "object": src})
                else:
                    self.notify({"success": False, "level": "file", "object": src})
                    self.notify({"success": False, "level": "folder"})
                    raise S3UploadError()

        self.notify({"success": "ok", "level": "folder"})

    def _upload(self, bucket_name, src, dst, extra_args=None):

        if extra_args is None:
            extra_args = dict()

        try:
            self._logger.info(f'S3: bucket: {bucket_name}, uploading: {dst}...')
            self._s3_client.upload_file(
                src, Bucket=bucket_name, Key=dst, ExtraArgs={**extra_args},
                Callback=self._progress(src) if self._progress else None
            )
            self._logger.info(f'S3: bucket: {bucket_name}, uploading: {dst} OK')
            return True
        except ValueError as e:
            self._logger.error(e)
            raise False
        except Exception as e:
            self._logger.error(e)
            self._logger.info(f'S3: bucket: {bucket_name}, uploading: {dst} NOK')
            return False

    def list(self, bucket: str, prefix: str = None) -> [dict]:
        try:
            contents = self._s3_client.list_objects(Bucket=bucket, Prefix=prefix)['Contents']
        except (KeyError, self._exceptions.NoSuchBucket):
            return []

        return contents

    def remove_bucket(self, bucket_name, _id):
        bucket = self._s3_resource.Bucket(bucket_name)
        bucket.objects.all().delete()
        return bucket.delete()

    def cold_action(self, action: str, container, _id):
        try:
            return getattr(self._s3_cold, action)(container, _id)
        except self._exceptions.NoSuchBucket:
            raise S3BucketError('Bucket does not exists or not configured')
        except AttributeError as e:
            raise S3BucketMethodNotImplemented(e)

    @staticmethod
    def list_source_objects(source_folder: str) -> [str]:
        path = Path(source_folder)
        paths = []

        for file_path in path.rglob("*"):
            if file_path.is_dir():
                continue
            str_file_path = str(file_path)
            str_file_path = str_file_path.replace(f'{str(path)}/', "")
            paths.append(str_file_path)

        return paths

    @staticmethod
    def _check_identical(obj, dst):

        try:
            dst_size = os.stat(dst).st_size
        except FileNotFoundError:
            dst_size = 0

        return obj['size'] == dst_size

    def notify(self, data):
        if self._callback:
            self._callback(**data)
