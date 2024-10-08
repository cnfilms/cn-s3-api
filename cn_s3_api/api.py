import os
from bisect import bisect_left
from logging import getLogger
from pathlib import Path

import boto3

from cn_s3_api.cold import S3ColdBucket
from cn_s3_api.exceptions import S3BucketError, S3UploadError, S3BucketMethodNotImplemented
from cn_s3_api.progress import ProgressPercentage
from cn_s3_api.utils import extract_obj_name
from botocore.exceptions import ClientError
from typing import Optional


class CNS3Api(object):
    def __init__(
            self,
            s3_config,
            progress=False,
            callback=None,
            logger=None
    ):
        self._s3_client = boto3.client('s3', **s3_config)
        self._s3_resource = boto3.resource('s3', **s3_config)
        self._s3_cold = S3ColdBucket(self._s3_client)

        self._exceptions = self._s3_client.exceptions
        self._callback = callback
        self._progress = ProgressPercentage if progress else None
        self._logger = getLogger() if not logger else logger

    def download(self, bucket_name, src, dst, skip_identical=True, extra_args=None):
        bucket = self._s3_resource.Bucket(bucket_name)

        try:
            objects = [dict(name=f.key, size=f.size) for f in bucket.objects.filter(Prefix=src)]
        except self._exceptions.NoSuchBucket as e:
            self.notify({"success": False, "level": "folder"})
            raise S3BucketError(e)

        if not objects:
            self._logger.info(f'S3: bucket: {bucket_name}, downloading: {src} NOK, no files to download')
            self.notify({"success": False, "level": "folder"})
            return

        if len(objects) == 1:
            if self._download(bucket, objects[0], dst, extra_args):
                self.notify({"success": True, "level": "file"})
            else:
                self.notify({"success": False, "level": "file"})

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
                self.notify({"success": True, "level": "file", "object": extract_obj_name(obj['name']),
                             "action": "download_object"})
                continue

            if self._download(bucket, obj, target, extra_args):
                self.notify({"success": True, "level": "file", "object": extract_obj_name(obj['name']),
                             "action": "download_object"})
            else:
                self.notify({"success": False, "level": "file", "object": extract_obj_name(obj['name']),
                             "action": "download_object"})
                all_downloads_ok = False

        self.notify({"success": all_downloads_ok, "level": "folder"})

    def _download(self, bucket, obj, dst, extra_args=None):
        src = obj['name']
        src_size = obj['size']

        if extra_args is None:
            extra_args = dict()

        try:
            self._logger.info(f'S3: bucket: {bucket.name}, downloading: {src}...')
            bucket.download_file(
                src, dst, **extra_args,
                Callback=self._progress(dst, obj_size=src_size, logger=self._logger) if self._progress else None
            )
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

        if not paths:
            self._logger.info(f'S3: bucket: {bucket_name}, uploading: {prefix} NOK, no files to upload')
            self.notify({"success": False, "level": "folder"})
            return

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
                    self.notify({"success": True, "level": "file", "object": extract_obj_name(dst),
                                 "status": 'uploaded'})
                else:
                    self.notify({"success": False, "level": "file", "object": extract_obj_name(dst)})
                    self.notify({"success": False, "level": "folder"})
                    raise S3UploadError()

        self.notify({"success": True, "level": "folder"})

    def _upload(self, bucket_name, src, dst, extra_args=None):

        if extra_args is None:
            extra_args = dict()

        try:
            self._logger.info(f'S3: bucket: {bucket_name}, uploading: {dst}...')
            self._s3_client.upload_file(
                src, Bucket=bucket_name, Key=dst, ExtraArgs={**extra_args},
                Callback=self._progress(filename=src, logger=self._logger) if self._progress else None
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

    def remove(self, bucket_name, prefix):
        bucket = self._s3_resource.Bucket(bucket_name)
        return bucket.objects.filter(Prefix=prefix).delete()

    def remove_objects(self, bucket_name, prefixes):

        bucket = self._s3_resource.Bucket(bucket_name)
        objects_list = []
        for prefix in prefixes:
            objects_to_delete = bucket.objects.filter(Prefix=prefix)
            objects_list.extend([{'Key': obj.key} for obj in objects_to_delete])

        if not objects_list:
            return {'not_found': True}
        try:
            return bucket.delete_objects(Delete={'Objects': objects_list})
        except Exception as e:
            self._logger.error(f"Exception occurred while deleting objects: {e}")
            raise e

    def remove_bucket(self, bucket_name, _id):
        bucket = self._s3_resource.Bucket(bucket_name)
        bucket.objects.all().delete()
        return bucket.delete()

    def cold_action(self, action: str, container, _id, prefix):
        try:
            return getattr(self._s3_cold, action)(container, _id, prefix)
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

    def create_presigned_url(self, bucket_name: str,
                             object_name: str,
                             expiration=3600) -> Optional[str]:
        """Generate a presigned URL to share an s3 object

        Arguments:
            bucket_name {str} -- Required. s3 bucket of object to share
            object_name {str} -- Required. s3 object to share

        Keyword Arguments:
            expiration {int} -- Expiration in seconds (default: {3600})

        Returns:
            Optional[str] -- Presigned url of s3 object. If error, returns None.
        """

        try:
            # note that we are passing get_object as the operation to perform
            response = self._s3_client.generate_presigned_url('get_object',
                                                              Params={
                                                                  'Bucket': bucket_name,
                                                                  'Key': object_name
                                                              },
                                                              ExpiresIn=expiration)
        except ClientError as e:
            self._logger.error(e)
            return None
        return response

    def copy_files(self, source_bucket, destination_bucket, object_name):
        """
        copy object from container A to B
        """
        try:
            self._s3_client.copy_object(
                Bucket=destination_bucket,
                CopySource={'Bucket': source_bucket, 'Key': object_name['from_object']},
                Key=object_name['to_object']
            )
            self._logger.info(f'S3: Copied {object_name["to_object"]} from {source_bucket} to {destination_bucket}')
            self.notify({"success": True, "action": "copy_object", "source_bucket": source_bucket,
                         "destination_bucket": destination_bucket, "destination_key": {object_name["to_object"]}})
        except ClientError as e:
            self._logger.error(f'Failed to copy  {object_name["from_object"]} from {source_bucket} '
                               f'to {destination_bucket}: {e}')
            self.notify({"success": False, "action": "copy_object", "source_bucket": source_bucket,
                         "destination_bucket": destination_bucket})
            raise

    def upload_file(self,  bucket_name, src, dst, extra_args=None):
        try:
            self._upload(bucket_name, src, dst, extra_args)
            self.notify({"success": True, "level": "file", "object": extract_obj_name(dst),
                         "status": 'uploaded'})
        except ClientError:
            self.notify({"success": False, "level": "file", "object": extract_obj_name(dst)})
            self.notify({"success": False, "level": "folder"})
            raise
