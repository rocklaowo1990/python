
import time
from server.util import Util
import boto3
from boto3.session import Session
from botocore.config import Config
from boto3.s3.transfer import TransferConfig
from botocore.exceptions import ClientError


class Aws:

    # 上传文件到S3，通过打开文件后上传
    def upload_s3(api_url: str, file_path: str, type: str, access_key: str, secret_key: str, region: str, bucket: str):
        session = Session(aws_access_key_id=access_key,
                          aws_secret_access_key=secret_key, region_name=region)

        s3 = session.resource("s3")
        upload_data = open(file_path, 'rb')
        file_md5 = Util.getFileMd5(file_path)
        upload_key = 'public/' + str(file_md5) + '.' + type

        print('正在检查文件是否存在: ' + file_path)
        files = session.client('s3').list_objects_v2(
            Bucket=bucket,
            Delimiter='/',
            Prefix=upload_key
        )

        if files['KeyCount'] != 0:
            print('文件已存在: ' + upload_key)
            return '1'

        print('正在上传文件：' + file_path +
              '：(' + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + ')')

        try:
            s3.Bucket(bucket).put_object(
                Key=upload_key, Body=upload_data, ACL='public-read')
            print('文件上传成功: ' + upload_key +
                  '：(' + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + ')')
            upload_data.close()
            return upload_key
        except Exception as e:
            print('上传文件出错：' + str(e))
            return '-1'

    # 路径上传
    def upload(api_url: str, file_path: str, type: str, access_key: str, secret_key: str, region: str, bucket: str):
        # 处理文件
        file_md5 = Util.getFileMd5(file_path)
        upload_key = 'public/' + str(file_md5) + '.' + type

        config = Config(s3={"use_accelerate_endpoint": True})
        # 当文件大小超过multipart_threshold属性的值时，会发生多部分传输 。
        # 如果文件大小大于TransferConfig对象中指定的阈值，以下示例将upload_file传输配置为分段传输。
        # 1GB=1024的三次方=1073741824字节
        MB = 1024 ** 2
        transfer_config = TransferConfig(
            multipart_threshold=100 * MB, max_concurrency=64, max_io_queue=1280)

        # aws 信息
        s3 = boto3.resource("s3", aws_access_key_id=access_key,
                            aws_secret_access_key=secret_key, region_name=region)

        # 检查文件是否存在
        print('正在检查文件是否存在: ' + file_path)
        try:
            s3.Object(bucket, upload_key).load()
            print('文件已存在: ' + upload_key)
            return '1'
        except ClientError as e:
            print('正在上传文件：' + file_path + '：(' +
                  time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + ')')

        try:
            # upload logo to s3，key_name指定S3上的路径，大于阀值分段传输
            s3.Bucket(bucket).upload_file(Filename=file_path, Key=upload_key, ExtraArgs={
                'ACL': 'public-read'}, Config=transfer_config)
            print('文件上传成功: public/' + upload_key + '：(' +
                  time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + ')')
            return upload_key
        except Exception as e:
            print('上传文件出错：' + str(e))
            return '-1'
