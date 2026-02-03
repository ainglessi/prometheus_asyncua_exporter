# SPDX-License-Identifier: Apache-2.0

# Copyright 2022 Sebastian Heppner, RWTH Aachen
# Copyright 2024 Alexander Inglessi, VDW e.V.

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

# http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
import yaml
from typing import List, Optional
import dataclasses
import asyncio
from asyncua import Client
import prometheus_client
import socket
import logging


@dataclasses.dataclass
class OPCUAGauge:
    metric_name: str
    node_path: str
    description: str
    gauge: prometheus_client.Gauge


# Read configuration and nodes from YAML file.
def read_yaml_config(filename: str) -> tuple:
    with open(filename, "r") as yaml_file:
        config = yaml.safe_load(yaml_file)
    exporter_port = config["exporter"].get("port", 9840)  # Read exporter port, default to 9840.
    servers_config = config["servers"]  # Read OPC UA servers and their nodes to be monitored.
    tls_certfile = config["exporter"].get("tls_certfile")  # Optional: TLS certificate file path.
    tls_keyfile = config["exporter"].get("tls_keyfile")  # Optional: TLS key file path.
    return exporter_port, servers_config, tls_certfile, tls_keyfile


# Configure logging
def configure_logging(filename: str):
    with open(filename, "r") as yaml_file:
        config = yaml.safe_load(yaml_file)
    log_level = config["exporter"].get("log_level", "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


async def query_server(
    url: str,
    username: Optional[str],
    password: Optional[str],
    nodes: List[dict],
    refresh_time: int,
):
    while True:
        try:
            async with Client(url=url) as opcua_client:
                # Set the username and password for authentication if provided.
                if username and password:
                    opcua_client.set_user(username)
                    opcua_client.set_password(password)
                for node in nodes:
                    try:
                        var = opcua_client.get_node(node["node_path"])
                        value = await var.read_value()
                        logging.info(f"Value of node [{var}]: {value}")
                        # Set the value to Prometheus gauge with label "server" set to server URL.
                        node["gauge"].labels(server=url).set(value)
                    except Exception as e:
                        logging.error(f"Error getting node value of {node['node_path']}: {e}")
                        # Set metric value to NaN when node not found or other errors occur.
                        node["gauge"].labels(server=url).set(float("NaN"))
        except socket.gaierror as e:
            logging.error(f"Error resolving hostname for OPC UA server {url}: {e}")
            # Set metric value to NaN when hostname resolution fails.
            for node in nodes:
                node["gauge"].labels(server=url).set(float("NaN"))
        except Exception as e:
            logging.error(f"Connection to OPC UA server {url} failed: {e}")
            # Set metric value to NaN when connection fails.
            for node in nodes:
                node["gauge"].labels(server=url).set(float("NaN"))
        await asyncio.sleep(refresh_time)


async def main():
    config_file = sys.argv[1] if len(sys.argv) > 1 else "config.yaml"
    exporter_port, servers_config, tls_certfile, tls_keyfile = read_yaml_config(config_file)
    configure_logging(config_file)
    # Start the Prometheus exporter with HTTP or HTTPS.
    if tls_certfile and tls_keyfile:
        logging.info(f"Starting HTTPS server on port {exporter_port}")
        prometheus_client.start_http_server(exporter_port, certfile=tls_certfile, keyfile=tls_keyfile)
    else:
        logging.info(f"Starting HTTP server on port {exporter_port}")
        prometheus_client.start_http_server(exporter_port)
    tasks = []
    # Cycle through OPC UA servers and nodes specified in config file.
    for server in servers_config:
        url = server["url"]
        username = server.get("username")
        password = server.get("password")
        refresh_time = server.get("refresh_time", 10)
        nodes = server.get("nodes", [])
        for node in nodes:
            metric_name = node["metric_name"]
            description = node.get("description", "")
            gauge = prometheus_client.Gauge(metric_name, description, labelnames=["server"])
            node["gauge"] = gauge
        tasks.append(asyncio.create_task(query_server(url, username, password, nodes, refresh_time)))
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
