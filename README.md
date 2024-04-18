# Fedi follow force graph

![App Status](https://img.shields.io/endpoint?url=https://fffg.scobiform.com/health)

<table>
  <tr>
    <td valign="top">
      <p>Mastodon analytics tool that generates a force graph to visually represent the relationships between user followers and followings on Mastodon. Users can log in via Mastodon OAuth to view graphs of their social connections. The tool is coded primarily in Python and utilizes JavaScript libraries for graphical representations.</p>
    </td>
    <td align="right" width="14%">
      <img src="https://github.com/Scobiform/fedi-follow-force-graph/blob/master/static/fffg_logo.svg" alt="Fedi follow force graph logo">
    </td>
  </tr>
</table>


## Table of Contents

- [Requirements](#requirements)
- [Environment Setup](#environment-setup)
- [Create Virtual Environment](#create-virtual-environment)
- [Start the Application](#start-the-application)
- [Mastodon Developer Settings](#mastodon-developer-settings)
- [Contributions](#contributions)
- [License](#license)

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

## Mastdodon developer settings

You will need a valid callback address that is reachable from the internet. You can use a service like [ngrok](https://ngrok.com/) to create a tunnel to your local machine.

## License

AGPL-3.0
