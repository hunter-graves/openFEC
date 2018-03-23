import logging

from celery_once import QueueOnce
from smart_open import smart_open
from webservices.tasks import app
from webservices.tasks import utils
from webservices import utils as web_utils
from webservices.env import env


logger = logging.getLogger(__name__)

@app.task(base=QueueOnce, once={'graceful': True})
def cache_all_requests(json_data, formatted_url):
    try:
        cached_url = 'cached-calls/{}'.format(formatted_url)
        s3_key = utils.get_s3_key(cached_url)

        # upload the json_data to s3 bucket
        with smart_open(cached_url, 'wb') as cached_file:
            cached_file.write(json_data)
        logger.info(
            'The following request has been uploaded to S3 successfully: {}'.format(
                cached_url
            )
        )
    except Exception as e:
        logger.error(
            'An exception occured while uploading the cached request to S3: {}'.format(e)
        )


@app.task
def delete_cached_calls_from_s3():
    """
    Deletes all files and folders under the cached-calls folder from S3.
    """
    bucket = utils.get_bucket()

    for obj in bucket.objects.filter(Prefix='cached-calls/'):
        obj.delete()

    slack_message = 'Successfully deleted the contents of the `cached-calls` folder in {0} from S3'.format(
        env.space
    )
    web_utils.post_to_slack(slack_message, '#bots')
    logger.info(slack_message)
