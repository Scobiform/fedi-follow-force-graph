import os
import hmac
import hashlib
import aiofiles
from mastodon import Mastodon
from app.configuration import ConfigurationManager

class SecretManager:
    '''Handles the management and verification of secrets for an application.'''

    def __init__(self):
        self.client_secret_path = 'client.secret'
        self.app_secret_path = 'app.secret'
        self.webhook_secret_path = 'webhook.secret'
        self.config = None

    @classmethod
    async def create(cls):
        instance = cls()
        configuration_manager = ConfigurationManager()
        instance.config = await configuration_manager.load_config()
        return instance

    async def get_or_create_app_secret(self):
        '''Get or create the app secret key asynchronously.'''
        if os.path.exists(self.app_secret_path):
            async with aiofiles.open(self.app_secret_path, 'r') as file:
                return await file.read()
        else:
            secret_key = self.generate_secret_key()
            async with aiofiles.open(self.app_secret_path, 'w', encoding='utf-8') as file:
                await file.write(secret_key)
            return secret_key
        
    def generate_secret_key(self):
        '''Generate a random secret key.'''
        return os.urandom(24).hex()

    def get_or_create_webhook_secret(self):
        '''Get or create the webhook secret key.'''
        if os.path.exists(self.webhook_secret_path):
            with open(self.webhook_secret_path, 'r') as file:
                return file.read()
        else:
            secret_key = self.generate_secret_key()
            with open(self.webhook_secret_path, 'w', encoding='utf-8') as file:
                file.write(secret_key)
            return secret_key

    def verify_signature(self, payload_body, github_signature):
        '''Verify the GitHub webhook signature.'''
        webhook_secret = self.get_or_create_webhook_secret().encode()
        computed_signature = 'sha256=' + hmac.new(webhook_secret, payload_body.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(github_signature, computed_signature)

    async def get_or_create_client_secret(self):
        '''Create secrets for the Mastodon API and manage configuration.'''
        redirect_uri = os.getenv('APP_URL')+'/callback'
        print(f"Redirect URI: {redirect_uri}")

        if not os.path.exists(self.client_secret_path):
            Mastodon.create_app(
                self.config['app_name'],
                api_base_url=self.config['instance_url'],
                redirect_uris=redirect_uri,
                to_file=self.client_secret_path
            )

        mastodon = Mastodon(
            client_id=self.client_secret_path,
            api_base_url=self.config['instance_url']
        )
        
        return mastodon

