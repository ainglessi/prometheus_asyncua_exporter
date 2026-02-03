# prometheus_asyncua_exporter

OPC UA exporter for Prometheus written in Python using [opcua-asyncio](https://github.com/FreeOpcUa/opcua-asyncio) and [prometheus-client](https://github.com/prometheus/client_python). Based on [prometheus_opcua_exporter](https://github.com/s-heppner/prometheus_opcua_exporter).

## Features

- Can read values of multiple nodes from multiple OPC UA servers.
  - Supports username+password authentication.
- Publishes values as Prometheus metrics (gauge type).
  - Optional TLS support.
- Returns NaN in case of errors.
- Can be run as a container.

## Usage

### Run natively

Clone this repository and install required libraries:

`python3 -m venv venv`

`source venv/bin/activate`

`pip install -r requirements.txt`

Adjust [config.yaml](config.yaml) to your needs and run the exporter with

`python3 exporter.py`

Prometheus metrics will then be available at <http://localhost:9840/>.

### Run in container

Build container image:

`docker build -t prometheus_asyncua_exporter .`

Edit `config.yaml` and start the container:

`docker run -v ./config.yaml:/app/config.yaml -p 9101:9840 prometheus_asyncua_exporter`

Or pull the pre-built package:

`docker run -v ./config.yaml:/app/config.yaml -p 9101:9840 ghcr.io/ainglessi/prometheus_asyncua_exporter`

Prometheus metrics will then be available at <http://localhost:9101/>.

## License

This software is distributed under [Apache License 2.0](LICENSE).
