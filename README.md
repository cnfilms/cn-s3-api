# CnS3Api, a python library for OVHCloud Object Storage

Lightweight python wrapper around OVHcloud Public Storage S3. Based on AWS boto3, it handles all the hard work including bucket transfers and OVH cold archive actions.

```python
from cn_s3_api.src.api import CNS3Api

s3_api = CNS3Api(dict(
    aws_access_key_id='xxxxxxxxxxxxxxxxxxxxxxxxx',
    aws_secret_access_key='xxxxxxxxxxxxxxxxxxxxxxxxx',
    endpoint_url='https://s3.rbx.io.cloud.ovh.net/',
    region_name='RBX',
))

s3_api.download('my-bucket', '/path_to_src_file', '/path_to_dst_file')
s3_api.upload('/path_to_src_file', 'my-bucket', '/path_to_dst_bucket_file')
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
pip install -e git+https://github.com/cnfilms/cn_s3_api.git
```

## Hacking

This wrapper uses standard Python tools, so you should feel at home with it.
Here is a quick outline of what it may look like. A good practice is to run
this from a ``virtualenv``.

## Get the sources

```bash
git clone https://github.com/ovh/python-ovh.git
cd python-ovh
python setup.py develop

```

You've developed a new cool feature? Fixed an annoying bug? We'd be happy
to hear from you!

## Run the tests

Simply run ``pytest``. It will automatically load its configuration from
``setup.cfg`` and output full coverage status. Since we all love quality, please
note that we do not accept contributions with test coverage under 100%.

```bash
pip install -e .[dev]
pytest
```

## License

3-Clause BSD
