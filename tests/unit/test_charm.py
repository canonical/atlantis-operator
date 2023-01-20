# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.
#
# Learn more about testing at: https://juju.is/docs/sdk/testing

import unittest

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

    def test_atlantis_pebble_ready(self):
        # Simulate the container coming up and emission of pebble-ready event
        self.harness.container_pebble_ready("atlantis")
        # Set required config
        self.harness.update_config(
            {
                "gh-token": "test",
                "gh-user": "test",
                "repo-allowlist": "github.com/myorg/*",
                "webhook-secret": "test",
            }
        )
        # Expected plan after Pebble ready with required config
        expected_plan = {
            "services": {
                "atlantis": {
                    "override": "replace",
                    "summary": "atlantis",
                    "command": "atlantis server --port=4141",
                    "startup": "enabled",
                    "environment": {
                        "ATLANTIS_ATLANTIS_URL": "atlantis",
                        "ATLANTIS_GH_TOKEN": "test",
                        "ATLANTIS_GH_USER": "test",
                        "ATLANTIS_GH_WEBHOOK_SECRET": "test",
                        "ATLANTIS_REPO_ALLOWLIST": "github.com/myorg/*",
                    },
                }
            },
        }
        # Get the plan now we've run PebbleReady
        updated_plan = self.harness.get_container_pebble_plan("atlantis").to_dict()
        # Check we've got the plan we expected
        self.assertEqual(expected_plan, updated_plan)
        # Check the service was started
        service = self.harness.model.unit.get_container("atlantis").get_service("atlantis")
        self.assertTrue(service.is_running())
        # Ensure we set an ActiveStatus with no message
        self.assertEqual(self.harness.model.unit.status, ActiveStatus())
