# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.
#
# Learn more about testing at: https://juju.is/docs/sdk/testing

import unittest
from unittest.mock import patch

import ops.testing
from ops.model import ActiveStatus
from ops.testing import Harness

from charm import AtlantisOperatorCharm


class TestCharm(unittest.TestCase):
    def setUp(self):
        # Enable more accurate simulation of container networking.
        # For more information, see https://juju.is/docs/sdk/testing#heading--simulate-can-connect
        ops.testing.SIMULATE_CAN_CONNECT = True
        self.addCleanup(setattr, ops.testing, "SIMULATE_CAN_CONNECT", False)

        self.harness = Harness(AtlantisOperatorCharm)
        self.addCleanup(self.harness.cleanup)
        self.harness.begin()

    def test_atlantis_required_data(self):
        # Simulate the container coming up and emission of pebble-ready event
        self.harness.container_pebble_ready("atlantis")
        # Confirm we're missing all config and our ingress-url
        self.assertEqual(
            self.harness.charm._required_data(),
            ["gh-token", "gh-user", "repo-allowlist", "webhook-secret", "ingress-url"]
        )
        # Set required config
        self.harness.update_config(
            {
                "gh-token": "test",
                "gh-user": "test",
                "repo-allowlist": "github.com/myorg/*",
                "webhook-secret": "test",
            }
        )
        # Confirm we're now just missing our ingress-url
        self.assertEqual(self.harness.charm._required_data(), ["ingress-url"])
