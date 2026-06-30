# SPDX-License-Identifier: Apache-2.0

"""Integration tests for the OPC UA authentication fix (bug #1).

These tests run against the public demo server at
``opc.tcp://opcua.umati.app:4843`` (user ``admin`` / password ``pw1``) and
require network access to that server.

They guard the fix in ``exporter.query_server`` where credentials must be set
on the ``asyncua.Client`` *before* entering its context manager, because the
context manager connects (and creates the authenticated session) on entry.
Setting ``set_user``/``set_password`` inside the ``async with`` block connects
an anonymous session and the credentials are silently ignored.

How the tests discriminate the fix
----------------------------------
The node used here (``Server.ServerDiagnostics.ServerDiagnosticsSummary.
CumulatedSessionCount``, ``ns=0;i=2278``) is:

* numeric and always > 0 on this server, so a successful authenticated read
  produces a value distinct from the Gauge default of ``0.0``;
* readable by an anonymous session.

The second property is what makes the wrong-credentials test a real regression
guard: with the fix, wrong credentials are sent during session creation and the
server rejects the session (``BadUserAccessDenied``), so the metric is set to
NaN. With the bug, wrong credentials are ignored, an anonymous session is
opened instead, the node is read anonymously, and the metric gets a real value
-- so the ``isnan`` assertion would fail and surface the regression.
"""

import asyncio
import contextlib
import math

import pytest
from prometheus_client import CollectorRegistry, Gauge

from exporter import query_server

UMATI_URL = "opc.tcp://opcua.umati.app:4843"
USER = "admin"
PASSWORD = "pw1"

# Server.ServerDiagnostics.ServerDiagnosticsSummary.CumulatedSessionCount.
NODE_PATH = "ns=0;i=2278"

# prometheus_client initializes a Gauge's labelled value to 0.0 before any
# .set() call; treat that as the "not yet read" sentinel while polling.
_UNSET = 0.0
_POLL_TIMEOUT = 25.0


def _gauge_value(gauge: Gauge, url: str) -> float:
    return gauge.labels(server=url)._value.get()


async def _wait_until_set(gauge: Gauge, url: str) -> float:
    """Poll until the gauge deviates from its initial value, or timeout."""
    loop = asyncio.get_event_loop()
    deadline = loop.time() + _POLL_TIMEOUT
    while loop.time() < deadline:
        value = _gauge_value(gauge, url)
        if value != _UNSET:
            return value
        await asyncio.sleep(0.5)
    return _gauge_value(gauge, url)


async def _run_one_cycle(url: str, user: str, password: str) -> float:
    """Run ``query_server`` for a single iteration and return the metric value."""
    registry = CollectorRegistry()
    gauge = Gauge(
        "umati_test_session_count",
        "CumulatedSessionCount via query_server",
        labelnames=["server"],
        registry=registry,
    )
    nodes = [{"node_path": NODE_PATH, "gauge": gauge}]
    # Large refresh_time so only the first iteration runs before we cancel.
    task = asyncio.create_task(
        query_server(url, user, password, nodes, refresh_time=3600)
    )
    try:
        value = await _wait_until_set(gauge, url)
    finally:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task
    return value


@pytest.mark.asyncio
async def test_correct_credentials_read_value():
    """Correct credentials open an authenticated session and read a value."""
    value = await _run_one_cycle(UMATI_URL, USER, PASSWORD)
    assert not math.isnan(value), f"expected a real value, got {value}"
    assert value > 0, f"expected a positive session count, got {value}"


@pytest.mark.asyncio
async def test_wrong_credentials_rejected():
    """Wrong credentials must be rejected at session creation (NaN metric).

    This is the regression guard for the fix: if credentials were set after
    connecting (the bug), an anonymous session would open instead and read the
    publicly-readable node, yielding a real value rather than NaN.
    """
    value = await _run_one_cycle(UMATI_URL, USER, "wrong-password")
    assert math.isnan(value), (
        "expected NaN because wrong credentials must be rejected during session "
        "creation; a real value means credentials were ignored (anonymous session)"
    )
