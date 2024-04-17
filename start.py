import asyncio
import logging
import os
import subprocess
import aiofiles
from dotenv import load_dotenv
from mastodon import Mastodon
from quart import Quart, abort, jsonify, render_template, render_template_string, request, redirect, session, url_for
from app.configuration import ConfigurationManager
from app.secrets import SecretManager
from app.websocket import ConnectionManager

# Load environment variables from .env file
load_dotenv() 

# Quart app
app = Quart(__name__)
config = None
graph_data = None

# Components
async def get_graph(graph_data):
    ''' Get the worker component and render it with the current configuration.'''
    return await render_template('graph.html', graph_data=graph_data)

async def generate_graph_data(user, followers, followings):
    # Add the authenticated user as the central node
    nodes = [{'id': user['id'], 'username': user['username']}]

    # Create nodes for followers with a type attribute
    nodes_followers = [{'id': u['id'], 'username': u['username'], 'avatar': u['avatar'], 'type': 'follower'} for u in followers]

    # Create nodes for followings with a different type attribute
    nodes_followings = [{'id': u['id'], 'username': u['username'], 'avatar': u['avatar'], 'type': 'following'} for u in followings]
    
    # Combine all nodes
    nodes += nodes_followers + nodes_followings

    # Create links from the central user to each follower and following
    links = [{'source': user['id'], 'target': follower['id']} for follower in followers]
    links += [{'source': user['id'], 'target': following['id']} for following in followings]

    #logging.info(f"Generated graph data: {nodes}, {links}")
    return {'nodes': nodes, 'links': links}

async def fetch_all_items(user, method):
    items = []
    max_id = None

    while True:
        response = method(user['id'], limit=500, max_id=max_id)
        items.extend(response)
        if len(response) < 500:
            break
        max_id = response[-1]['id']

    # Logging
    logging.info(f"Method: {method}")
    logging.info(f"User: {user}")
    logging.info(f"Items length: {len(items)}")

    return items

# Async setup function to load configs and create secrets
@app.before_serving
async def setup_app():
    global secret_manager
    secret_manager = await SecretManager.create() # Secret manager for the application
    global configuration_manager
    configuration_manager = ConfigurationManager() # Configuration manager for the application
    webhook_secret = await secret_manager.get_or_create_webhook_secret()
    app.secret_key = await secret_manager.get_or_create_app_secret()
    global config
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
        # Initialize Mastodon with the access token
        mastodon = Mastodon(
            access_token=session['access_token'],
            api_base_url=config['instance_url']
        )

        # Fetch the authenticated user
        user = mastodon.account_verify_credentials()

        # Pass data to the template
        return await render_template('index.html', logged_in=True, user=user)
    else:
        # Render the template without user data
        return await render_template('index.html', logged_in=False)
    
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
        repo_path = os.getenv('REPO_PATH')
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
    asyncio.run(app.run(host='localhost', port=5003, debug=False))

