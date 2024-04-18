# Fedi follow force graph

![App Status](https://img.shields.io/endpoint?url=https://fffg.scobiform.com/health)

Mastodon analytics tool. It will create a force graph based on user followers and followings.

## Requirements

```plaintext

Python
    dotenv
    mastodon.py
    quart

JavsScript
    force-graph
    d3-quadtree
    d3-force
    element-resize-detector
```

## Environment Setup

Create a `.env` file with the following content to configure the application:

```plaintext
APP_URL=https://yourdomain
REPO_PATH=/path/to/repo
```

## Create virtual environment

Create a virtual environment and install the requirements:

```plaintext
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Start the application

```plaintext
python3 start.py
```
