import os
import json

class DB:

    def __init__(self) -> None:
        self.data_path='data.json'
        self.data={}

        if os.path.exists(self.data_path):
            with open(self.data_path, 'r') as file:
                self.data = json.load(file)

    def get_projects(self) -> list | None:
        if len(self.data) > 0:
            return self.data
        return None
    
    def get_project(self, vk_group_id):
        for project in self.data:
            if project['vk_group_id'] == vk_group_id:
                return project
            
    def set_description(self, vk_group_id, description):
        for i, project in enumerate(self.data):
            if project['vk_group_id'] == vk_group_id:
                self.data[i]['description'] = description
    
    def set_last_video_time(self, vk_group_id, channel_name, last_time) -> None:
        for i, project in enumerate(self.data):
            if project['vk_group_id'] == vk_group_id:
                for j, tiktok_channel in enumerate(project['tiktok_channels']):
                    if channel_name in tiktok_channel['channel_name']:
                        self.data[i]['tiktok_channels'][j]['last_video_time'] = last_time
        self.save()

    def save(self):
        with open(self.data_path, 'w') as file:
            file.write(json.dumps(self.data))

    def set_project(self, new_project):
        if len(self.data) == 0:
            self.data = []
        
        for i, project in enumerate(self.data):
            if project['vk_group_id'] == new_project['vk_group_id']:
                self.data.pop(i)

        self.data.append(new_project)

    def set_tiktok_account(self, vk_group_id, new_tiktok_channel):
        for i, project in enumerate(self.data):
            if project['vk_group_id'] == vk_group_id:
                tiktok_channels = [tiktok_channel['channel_name'] for tiktok_channel in project['tiktok_channels']]
                
                if not new_tiktok_channel in tiktok_channels:
                    self.data[i]['tiktok_channels'].append({
                            'channel_name': new_tiktok_channel,
                            'last_video_time': 0
                        })
    
    def delete_project(self, vk_group_id):
        for i, project in enumerate(self.data):
            if project['vk_group_id'] == vk_group_id:
                self.data.pop(i)

    def delete_tiktok_from_project(self, vk_group_id, tiktok_id):
        for i, project in enumerate(self.data):
            if project['vk_group_id'] == vk_group_id:
                for j, tiktok_channel in enumerate(project['tiktok_channels']):
                    if tiktok_id in tiktok_channel['channel_name']:
                        self.data[i]['tiktok_channels'].pop(j)
