import json
import os
import aiofiles
import logging

class ConfigurationManager:
    '''Class to manage configuration settings asynchronously using the singleton pattern.'''

    _instance = None

    def __init__(self, filename='config/settings.json'):
        self.filename = filename
        self.configuration = {}

    @classmethod
    async def create(cls, filename='config/settings.json'):
        if cls._instance is None:
            cls._instance = cls(filename)
            await cls._instance.load_config()
        return cls._instance

    async def load_config(self, filename='config/settings.json'):
        try:
            async with aiofiles.open(filename, 'r') as file:
                return json.loads(await file.read())
        except Exception as e:
            print(f"Failed to load configuration: {e}")
            return {}

    def default_configuration(self):
        return {
            # The name of your application
            "app_name": "Fedi follow force graph",

            # The Mastodon instance URL where the app will operate
            "instance_url": "mastodon.social",

            # User's email for login to Mastodon
            "mastodon_email": "your-email@example.com",

            # User's password for login to Mastodon
            "mastodon_password": "your-password",

            # Path to the application repository on the server
            "repo_path": "/path/to/your/repository",

            # Logging configuration
            "logging": {
                "filename": "_.log",
                "filemode": "a",
                "format": "%(asctime)s - %(levelname)s - %(message)s",
                "level": "INFO"
            }
        }

    async def save_config(self):
        ''' Save the configuration settings to the configuration file. '''
        try:
            config_str = json.dumps(self.configuration, ensure_ascii=False, indent=4)
            async with aiofiles.open(self.filename, 'w', encoding='utf-8') as file:
                await file.write(config_str)
            print(f"Configuration saved to {self.filename}.")
            await self.load_config()
        except Exception as e:
            print(f"Failed to save {self.filename}: {e}")

    async def update_config(self, new_data):
        self.configuration.update(new_data)
        await self.save_config()

    async def update_config_value(self, key, value):
        ''' Update a configuration setting with a new value.

            Args:
            key (str): The key of the setting to update.
            value (str): The new value of the setting.

        '''
        try:
            self.configuration[key] = value
            async with aiofiles.open(self.filename, mode='w', encoding='utf-8') as file:
                await file.write(json.dumps(self.configuration, indent=4))
        except Exception as e:
            logging.error(f"Failed to update configuration: {e}")
