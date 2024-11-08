# Fedi follow force graph

[![CodeQL](https://github.com/Scobiform/fedi-follow-force-graph/actions/workflows/github-code-scanning/codeql/badge.svg)](https://github.com/Scobiform/fedi-follow-force-graph/actions/workflows/github-code-scanning/codeql)
![App Status](https://img.shields.io/endpoint?url=https://fffg.scobiform.com/health)


<img src="https://github.com/Scobiform/fedi-follow-force-graph/blob/master/static/fffg_logo.svg" alt="fedi follow force graph logo" align="right" style="width: 14%"/>

Mastodon analytics tool that generates a force graph to visually represent the relationships between user followers and followings on Mastodon. Users can log in via Mastodon OAuth to view graphs of their social connections. The tool is coded primarily in Python and utilizes JavaScript libraries for graphical representations.

## Table of Contents

- [Requirements](#requirements)
- [Environment Setup](#environment-setup)
- [Create Virtual Environment](#create-virtual-environment)
- [Start the Application](#start-the-application)
- [Mastodon Developer Settings](#mastodon-developer-settings)
- [Contributions](#contributions)
- [Screenshots](#screenshots)
- [License](#license)

## Requirements

```plaintext

Python:
    dotenv - BSD-3-Clause License
    Mastodon.py - AGPL-3.0 License
    Quart - MIT License
    Quart-Auth - MIT License

JavaScript:
    force-graph - MIT License
    d3-quadtree - BSD-3-Clause License
    d3-force - BSD-3-Clause License
    element-resize-detector - MIT License

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

Run the application with the following command:

```plaintext

python3 start.py

```

## Mastdodon developer settings

You will need a valid callback address that is reachable from the internet. You can use a service like [ngrok](https://ngrok.com/) to create a tunnel to your local machine.

## Contributions

Contributions are welcome! Please submit a pull request or open an issue if you would like to contribute to the project.

## Screenshots

<img src="https://github.com/Scobiform/fedi-follow-force-graph/blob/master/static/screen.png" alt="fedi follow force graph screen" style="width: 100%"/>

## License

AGPL-3.0

## Do not use this in production

This is a proof of concept and should not be used in production. The application has not been tested for security vulnerabilities.
