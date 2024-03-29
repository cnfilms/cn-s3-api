# Python library for OVHCloud Object Storage managment

Lightweight python wrapper around OVHcloud Public Storage S3. Based on AWS boto3, it handles all the hard work including bucket transfers and OVH cold archive actions.

```python
from cn_s3_api.api import CNS3Api

s3_api = CNS3Api(dict(
    aws_access_key_id='xxxxxxxxxxxxxxxxxxxxxxxxx',
    aws_secret_access_key='xxxxxxxxxxxxxxxxxxxxxxxxx',
    endpoint_url='https://s3.rbx.io.cloud.ovh.net/',
    region_name='RBX',
))

s3_api.download('my-bucket', '/path_to_src_file', '/path_to_dst_file')
s3_api.upload('my-bucket', '/path_to_src_file', '/path_to_dst_bucket_file')
s3_api.list('my-bucket')
s3_api.list('my-bucket', '/path_to_dst_bucket_dir')

s3_api.cold_action('archive', 'my-bucket', 'bucket-id')
s3_api.cold_action('status', 'my-bucket', 'bucket-id')
s3_api.cold_action('restore', 'my-bucket', 'bucket-id')
```

## Installation

The python wrapper works with Python 3.6+.

The easiest way to get the latest stable release is to grab it from pypi using pip.

```
pip install cn_s3_api
```

Alternatively, you may get latest development version directly from Git.

```
pip install -e git+https://github.com/cnfilms/cn-s3-api.git
```

## Hacking

This wrapper uses standard Python tools, so you should feel at home with it.
Here is a quick outline of what it may look like. A good practice is to run
this from a ``virtualenv``.

## Get the sources

```bash
git clone https://github.com/cnfilms/cn-s3-api.git
cd cn-s3-api
python setup.py develop

```

## Run the tests

Simply run ``pytest``. It will automatically load its configuration from ``setup.cfg`` and output full coverage status. 

```bash
pip install -e .
pytest
```

## Contributing

If you find a bug :bug:, please open a [bug report](https://github.com/cnfilms/cn-s3-api/issues/new?assignees=&labels=bug&template=bug_report.md&title=).
If you have an idea for an improvement or new feature :rocket:, please open a [feature request](https://github.com/cnfilms/cn-s3-api/issues/new?assignees=&labels=Feature+request&template=feature_request.md&title=).

## License

3-Clause BSD
