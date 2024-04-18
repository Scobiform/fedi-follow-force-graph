# Fedi follow force graph

![App Status](https://img.shields.io/endpoint?url=https://fffg.scobiform.com/health)

Mastodon analytics tool that generates a force graph to visually represent the relationships between user followers and followings on Mastodon. Users can log in via Mastodon OAuth to view graphs of their social connections. The tool is coded primarily in Python and utilizes JavaScript libraries for graphical representations.

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
