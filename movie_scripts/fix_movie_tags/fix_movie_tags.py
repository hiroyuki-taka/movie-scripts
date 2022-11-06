from typing import Iterable

import boto3
from mypy_boto3_s3.service_resource import ObjectSummary

s3_resource = boto3.resource("s3")
s3_client = boto3.client("s3")


class FixMovieTags:
    def __init__(self):
        self.bucket_name = "movie-backup-538347644889"
        self.bucket = s3_resource.Bucket(self.bucket_name)
        self.bucketTagging = s3_resource.BucketTagging(self.bucket_name)

    def s3_file_list(self) -> Iterable[ObjectSummary]:
        for fileobj in self.bucket.objects.all():
            yield fileobj

    def fix_movie_tags(self):
        for fileobj in self.s3_file_list():
            if fileobj.size < 10 * 1024 * 1024 or fileobj.storage_class == "GLACIER":
                continue

            bucket_name = fileobj.Bucket().name
            file_key = fileobj.key

            tags: list[dict[str, str]] = s3_client.get_object_tagging(
                Bucket=bucket_name, Key=file_key
            ).get("TagSet", [])
            object_types: list[str] = [x['Value'] for x in tags if x['Key'] == 'object-type']

            if not object_types:
                tags.append({'Key': 'object-type', 'Value': 'movie'})
                s3_client.put_object_tagging(Bucket=bucket_name, Key=file_key, Tagging={"TagSet": tags})
                print(f"[INFO] tagを更新します key={file_key}, tags={tags}")


if __name__ == '__main__':
    FixMovieTags().fix_movie_tags()
