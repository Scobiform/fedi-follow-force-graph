# Fedi follow force graph

![App Status](https://img.shields.io/endpoint?url=https://fffg.scobiform.com/health)

Mastodon analytics tool. It will create a force graph based on user followers and followings. 

## Requirements
dotenv
mastodon.py
quart

## Environment Setup

Create a `.env` file with the following content to configure the application:

```plaintext
APP_URL=https://yourdomain
REPO_PATH=/path/to/repo
```

## Create virtual environment

Create a virtual environment and install the requirements:

```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
``` 

## Start the application

```
python3 start.py
```

