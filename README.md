# Resource Usage Tracker

This project is a Python-based application designed to track and notify resource usage of a specified script. It integrates with a Streamlit app for visualization and provides notifications at specified intervals.

## Features

- **Run Python Scripts**: Execute a specified Python script and track its resource usage.
- **Streamlit Integration**: Launch a Streamlit app for visualizing resource usage.
- **Notifications**: Receive notifications about resource usage at configurable intervals.
- **Logging**: Logs process information and errors to a file.

## Prerequisites

- Python 3.x
- Streamlit
- ConfigParser
- NotifierApp and StreamlitApp modules

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Ensure you have a configuration file at `configs/config.conf` with the necessary settings.

## Configuration

The application uses a configuration file located at `configs/config.conf`. Ensure it contains the following sections:

```ini
[LOGGER]
LEVEL = INFO

[NOTIF_SETTING]
NOTIFICATION_INTERVAL = 1  # in hours
```

## Usage

To run the application, use the following command:

```bash
python main.py -p <script_name>
```
for running without a python process:
```bash
python main.py
```

- `-p`, `--script`: (Optional) The name or path of the Python script to run. If not provided, only the Streamlit app will be launched.

## Logging

Logs are stored in `logging/log.txt`. The logging level can be configured in the `configs/config.conf` file.

