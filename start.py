import asyncio
import logging
import os
import re
import subprocess
import aiofiles
from dotenv import load_dotenv
from mastodon import Mastodon
from quart import Quart, abort, jsonify, render_template, render_template_string, request, redirect, session, url_for
from quart_auth import AuthUser, QuartAuth, login_required, login_user, logout_user
from app.configuration import ConfigurationManager
from app.secrets import SecretManager
from app.websocket import ConnectionManager

# Project
# https://github.com/users/Scobiform/projects/7/views/1

# Load environment variables from .env file
load_dotenv() 

# Quart app
app = Quart(__name__)
config = None
graph_data = None

# Components
async def get_graph(user, instance):
    ''' Pass the user data to the template.'''
    return await render_template('graph.html', user=user, api_base_url=os.getenv('APP_URL'), instance=instance)

@app.before_serving
async def setup_app():
    ''' Setup the application before serving requests.'''
    global secret_manager
    secret_manager = await SecretManager.create() # Secret manager for the application
    global configuration_manager
    configuration_manager = ConfigurationManager() # Configuration manager for the application
    webhook_secret = await secret_manager.get_or_create_webhook_secret()
    app.secret_key = await secret_manager.get_or_create_app_secret()
    global config
    config = await configuration_manager.load_config()
    global websocket
    websocket = ConnectionManager()

    # Mastodon client
    global mastodon
    mastodon = await secret_manager.get_or_create_client_secret()

    # Auth
    QuartAuth(app)

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
    ''' Home route for the application.'''
    if 'access_token' in session:
        # Initialize Mastodon with the access token
        mastodon = Mastodon(
            access_token=session['access_token'],
            api_base_url=config['instance_url']
        )

        # Fetch the authenticated user
        global user
        user = mastodon.account_verify_credentials()

        # Pass the user to the template
        graph_component = await get_graph(user, instance=config['instance_url'])

        app_name =  config['app_name']
        app_url = os.getenv('APP_URL')

        # Pass data to the template
        return await render_template('index.html', logged_in=True, user=user, graph=graph_component, app_name=app_name, app_url=app_url)
    else:
        # Render the template without user data
        return await render_template('index.html', logged_in=False)

@app.route('/login')
async def login():
    ''' Login route for the application.'''
    redirect_uri = os.getenv('APP_URL')+'/callback'
    return redirect(mastodon.auth_request_url(scopes=['read', 'write'], redirect_uris=redirect_uri))

@app.route('/logout')
async def logout():
    ''' Logout route for the application.'''
    session.pop('access_token', None)
    # Log the user out
    logout_user()

    return redirect(url_for('home'))

@app.route('/callback')
async def callback():
    ''' Callback route for the application.'''
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

        # Fetch the authenticated user
        user = mastodon.account_verify_credentials()

        # Create a QuartAuth user and log them in
        auth_user = AuthUser(str(user.id))
        login_user(auth_user)
        
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
    ''' Webhook route for the application.'''
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

@app.websocket("/ws")
@login_required
async def ws():
    current_ws = websocket._get_current_object()
    websocket.add_connection(current_ws)
    try:
        while True:
            # Receive a message from the client
            message = await websocket.receive()
            # Broadcast the message to all connected clients
            await websocket.broadcast_message(message)
    except:
        # Handle exceptions, e.g., client disconnecting
        await websocket.broadcast_message("Client disconnected.")
        pass
    finally:
        websocket.remove_connection(current_ws)

@app.route('/user', methods=['GET'])
@login_required
async def fetch_user():
    ''' Fetch a user from the instance.'''
    user_id = request.args.get('user_id', type=int)
    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400

    try:
        user = mastodon.account(user_id)
        return jsonify(user)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/followers', methods=['GET'])
@login_required
async def fetch_followers():
    ''' Fetch the followers of a user.'''
    user_id = request.args.get('user_id', type=int)
    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400

    try:
        followers = mastodon.account_followers(user_id, limit=420)
        all_followers = followers

        while followers:
            followers = mastodon.fetch_next(followers)
            if followers:
                all_followers.extend(followers)

        return jsonify(all_followers)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/following', methods=['GET'])
@login_required
async def fetch_following():
    ''' Fetch the users that a user is following.'''
    user_id = request.args.get('user_id', type=int)
    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400

    try:
        following = mastodon.account_following(user_id, limit=420)
        all_following = following

        while following:
            following = mastodon.fetch_next(following)
            if following:
                all_following.extend(following)

        return jsonify(all_following)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/search', methods=['GET'])
@login_required
async def search():
    ''' Search for users on the instance.'''
    # session['access_token']

    instance = request.args.get('instance')
    instance = re.search(r"//([^/@]+)", instance).group(1) if re.search(r"//([^/@]+)", instance) else None

    query = request.args.get('query')
    if not query:
        return jsonify({'error': 'Query is required'}), 400

    if 'access_token' not in session:
            return jsonify({'error': 'Authentication required'}), 401

    mastodon = Mastodon(
        access_token=session['access_token'],
        api_base_url=instance
    )

    try:
        results = mastodon.account_search(query, limit=420)

        # Filter results for same instance as user
        #results = [result for result in results if re.search(r"//([^/@]+)", result['url']).group(1) == instance]
        # Filter results for indexable accounts
        #results = [result for result in results if result['discoverable'] == True]

        
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    ''' Run the application.'''
    asyncio.run(app.run(host='localhost', port=5003, debug=False))

