import redis
import os
import requests
from celery import Celery, Task
from celery.result import AsyncResult

from ..external import ExternalException
#from ..model.credibility_manager import celery
#from ..model.credibility_manager import get_tweet_credibility_from_id

GATEWAY_MODULE_ENDPOINT = os.environ.get('GATEWAY_MODULE_ENDPOINT', 'https://localhost:1234/foo')
REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')

r = redis.Redis(host=REDIS_HOST)
r.set('test','test')
celery = Celery('tasks', broker=f'redis://{REDIS_HOST}:6379/0', backend=f'redis://{REDIS_HOST}:6379/0')
print('redis OK')

celery.conf.update(
    task_serializer='pickle', # so that the wrapper can have the function as an argument (not serializable through json)
    accept_content=['json', 'pickle']
    #result_serializer='pickle'
)


class CallbackTask(Task):
    def on_success(self, retval, job_id, args, kwargs):
        print('task succeeded, submitting to the gateway', job_id)
        callback_url = get_mapping(job_id)
        if callback_url:
            callback_url = callback_url.decode('utf-8')
        else:
            callback_url = ''
        print(callback_url)
        # TODO here we walidate the callback_url
        response_object = {
            'response': retval
        }
        if not 'api.coinform.eu/' in callback_url:
            print('callback_url not valid')
            return
        try:
            response = requests.post(callback_url, json=response_object, verify=False)
            print(response.status_code)
        except Exception as e:
            print(e)
            print('error submitting to gateway')

    def on_failure(self, exc, job_id, args, kwargs, einfo):
        pass


@celery.task(base=CallbackTask, bind=True)# TODO(bind=True) will have self.update_state() to let the user to have more details https://blog.miguelgrinberg.com/post/using-celery-with-flask
def wrapper(self, time_demanding_fn, *args, **kwargs):
    print('job_id', wrapper.request.id, time_demanding_fn)
    # TODO add a function to be called each time that an update comes, and call self.update_state() with bind=True
    tell_me_your_status = lambda message: self.update_state(state = message)
    result = time_demanding_fn(update_status_fn=tell_me_your_status, *args, **kwargs)
    try:
        response = requests.post(GATEWAY_MODULE_ENDPOINT, json=content)
        print(response.status_code)
    except:
        print('error submitting to gateway')
    return result

def create_task_for(*args, **kwargs):
    """This creates a task"""
    print('submitting task')
    #app.stuff.delay()
    callback_url=kwargs.get('callback_url')
    if callback_url:
        del kwargs['callback_url']
    job = wrapper.apply_async(args=args, kwargs=kwargs)
    if callback_url:
        # save the mappings, so that we can then retrieve the job by callback url
        r.set(callback_url, job.id)
        r.set(job.id, callback_url)
    return {
        'job_id': job.id,
        'callback_url': callback_url
    }



def get_task_status(job_id):
    task = AsyncResult(id=job_id, app=celery)
    #task = get_tweet_credibility_from_id.AsyncResult(job_id)
    if task.state == 'PENDING':
        # job did not start yet
        response = {
            'state': task.state,
        }
    elif task.state != 'FAILURE':
        response = {
            'state': task.state,
        }
        # if 'result' in task.info:
        #     response['result'] = task.info['result']
        if task.state == 'SUCCESS':
            response['result'] = task.get()
    else:
        # something went wrong in the background job
        response = {
            'state': task.state,
            'status': str(task.info),  # this is the exception raised # TODO get status_code propagated and detail attribute
            'error': {}
        }
        if isinstance(task.info, ExternalException):
            # this is (http_status_code, json object)
            response['error'] = task.info.json_error
            response['error']['http_status_code'] = task.info.status_code
    return response

def get_mapping(key):
    """Works bidirectionally"""
    return r.get(key)

def get_task_status_from_callback_url(callback_url):
    job_id = r.get(callback_url)
    if not job_id:
        return None
    return get_task_status(job_id)

def health():
    return r.echo('ok').decode()
