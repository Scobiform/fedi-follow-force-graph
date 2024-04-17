import logging
import os
import subprocess
from dotenv import load_dotenv
from mastodon import Mastodon
from quart import Quart, abort, jsonify, request, redirect, session, url_for
from app.configuration import ConfigurationManager
from app.secrets import SecretManager
from app.websocket import ConnectionManager

# Load environment variables from .env file
load_dotenv() 

# Quart app
app = Quart(__name__)
config = None

# Async setup function to load configs and create secrets
@app.before_serving
async def setup_app():
    global secret_manager
    secret_manager = await SecretManager.create() # Secret manager for the application
    global configuration_manager
    configuration_manager = ConfigurationManager() # Configuration manager for the application
    webhook_secret = secret_manager.get_or_create_webhook_secret()
    app.secret_key = await secret_manager.get_or_create_app_secret()
    config = await configuration_manager.load_config()

    # Mastodon client
    global mastodon
    mastodon = await secret_manager.get_or_create_client_secret()

    # Logging
    logging_config = config['logging']
    logging.basicConfig(
        filename='log/'+logging_config['filename'],
        filemode='a',
        format=logging_config['format'],
        level=getattr(logging, logging_config['level'])
    )

@app.route('/')
async def home():
    if 'access_token' in session:
        return '''
        Logged in successfully! <br>
        <a href="/logout">Logout</a>
        '''
    return '<a href="/login">Login with Mastodon</a>'
    
@app.route('/login')
async def login():
    redirect_uri = os.getenv('APP_URL')+'/callback'
    return redirect(mastodon.auth_request_url(scopes=['read', 'write'], redirect_uris=redirect_uri))

@app.route('/logout')
async def logout():
    session.pop('access_token', None)
    return redirect(url_for('home'))

@app.route('/callback')
async def callback():
    code = request.args.get('code')
    if not code:
        return "Authorization failed: No code provided.", 400
    try:
        redirect_uri = os.getenv('APP_URL')+'/callback'
        print(f"Redirect URI: {redirect_uri}")

        access_token = mastodon.log_in(
            code=code, 
            scopes=['read', 'write'],
            redirect_uri= redirect_uri
        )

        # Save the access token in the session
        session['access_token'] = access_token
        return redirect(url_for('home'))
    except Exception as e:
        logging.error(f"Login error: {e}")
        return f"Error during login: {str(e)}", 500

@app.route('/health')
async def health():
    ''' Check the health of the application.'''
    app_status = 'up'
    color = "brightgreen" if app_status == "up" else "red"
    return jsonify(
        {
            "schemaVersion": 1,
            "label": "app status",
            "message": app_status,
            "color": color
        }
)

@app.route('/webhook', methods=['POST'])
async def webhook():
    github_signature = request.headers.get('X-Hub-Signature-256', '')
    payload_body = await request.get_data()  # Get the raw byte payload for signature computation
    # Verify the signature
    if not await secret_manager.verify_signature(payload_body, github_signature):
        print("Signature verification failed.")
        abort(401) # Unauthorized
    # If the signature is verified, process the webhook payload
    payload = await request.json
    # Check if the push is to the master branch
    if payload['ref'] == 'refs/heads/master':
        repo_path = config['repo_path']
        # Fetch and reset the local repository to match the remote
        try:
            # Fetch the latest changes from the remote
            subprocess.run(['git', '-C', repo_path, 'fetch', 'origin', 'master'], check=True)
            # Reset the local branch to match the remote, discarding any local changes
            subprocess.run(['git', '-C', repo_path, 'reset', '--hard', 'origin/master'], check=True)
            logging.info("Repository successfully updated.")
        except subprocess.CalledProcessError as e:
            logging.info(f"Failed to update repository: {e}")
        return 'OK'
    else:
        return 'Push was not to master branch', 200

if __name__ == '__main__':
    app.run(host='localhost', port=5003, debug=False)

