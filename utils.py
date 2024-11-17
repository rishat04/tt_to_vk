import asyncio
import config
import requests
import random
import string
import logging
import time
import os

from db import DB
from requests_toolbelt import MultipartEncoder
from os.path import getsize

from TikTokApi import TikTokApi

from download_tiktok_videos import DownloadTikTokVideos

logger = logging.getLogger(__name__)

def get_tiktok_videos_v1(username):
    cookies = get_tiktok_cookies(username)
    print(cookies)
    logger.debug('starting get videos links.. [tiktok]')
    msToken=config.msToken
    videos = []
    async def get():
        async with TikTokApi() as api:
            await api.create_sessions(cookies=[cookies], num_sessions=1, sleep_after=3)
            logger.debug('get user.. [tiktok]')
            user = api.user(username)
            async for video in user.videos(count=5):
                video_id = video.as_dict['id']
                if video_id:
                    videos.append({'video_link': f'https://www.tiktok.com/@{username}/video/{video_id}', 'createTime': video.as_dict['createTime']})
    asyncio.run(get())
    return videos if videos else None

def get_tiktok_cookies(username):
    session = requests.Session()
    r=session.get(f'https://www.tiktok.com/@{username}')
    return r.cookies.get_dict()

def get_vk_group_id(url):
    logger.debug('extracting vk group id.. [vk]')
    vk_group = url.split('https://vk.com/')[1].rstrip('/')
    url = f'https://api.vk.com/method/groups.getById?v=5.92&group_id={vk_group}&access_token={config.token}'
    r = requests.get(url)
    return r.json()['response'][0]['id']

def upload_video_vk(file_path, description: str, group_id: int):
    logger.debug('uploading video to.. [vk]')
    r = requests.post("https://api.vk.com/method/shortVideo.create", data=dict(v=5.132,
                                                                               can_make_duet=0,
                                                                               description=description,
                                                                               group_id=group_id,
                                                                               file_size=getsize(file_path),
                                                                               access_token=config.token))
    if not 'response' in r.json():
        return False
    
    upload_url = r.json()["response"]["upload_url"]
    fields = {
        'file': ('untitiled.mp4', open(file_path, "rb"), "video/mp4"),
    }
    boundary = '----WebKitFormBoundary' + ''.join(random.sample(string.ascii_letters + string.digits, 16))
    m = MultipartEncoder(fields=fields, boundary=boundary)
    r = requests.post(upload_url, data=m,
                      headers={"user-agent": "vk-test-clip-upload 1", "Content-Type": m.content_type})
    
    if r.status_code == 200 and r.text == '<retval>1</retval>':
        return True
    
    return False

def get_tiktok_username(url):
    url = url.split('tiktok.com/@')[1]
    return url.split('/')[0] if '/' in url else url.split('?')[0].rstrip('/')

def proccess():
    print('starting proccess...')
    path = 'downloaded'

    if not os.path.exists(path):
        os.mkdir(path)

    downloader = DownloadTikTokVideos()
    db = DB()

    projects = db.get_projects()
    if not projects:
        return
    
    for project in projects:
        vk_group_id = project['vk_group_id']
        description = project['description']

        for tiktok_channel in project['tiktok_channels']:
            tiktok_account = tiktok_channel['channel_name']
            last_video_time = tiktok_channel['last_video_time']

            try:
                print(f'get tiktok links for {tiktok_account}')
                videos = get_tiktok_videos_v1(tiktok_account)
            except Exception as e:
                print("can't get videos from tiktok")
                print("waiting 1 minute")
                time.sleep(60)
                continue
            
            if not videos:
                print('cant get videos from tiktok page')
                continue

            if not last_video_time and videos:
                videos = videos[:1]
                
            videos.reverse()
            
            for video in videos:
                if video['createTime'] <= last_video_time:
                    continue
                
                video_path = downloader.download_video(video['video_link'], path)
                
                time.sleep(5)

                is_uploaded = upload_video_vk(video_path, description, vk_group_id)

                if is_uploaded:
                    db.set_last_video_time(vk_group_id, tiktok_account, video['createTime'])
                else:
                    print('cant upload video to vk')
                    if os.path.exists(video_path):
                        os.remove(video_path)
                    return

                if os.path.exists(video_path):
                    os.remove(video_path)

if __name__ == '__main__':
    proccess()
