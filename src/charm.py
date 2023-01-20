#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.
"""Charm for Atlantis on kubernetes."""

import json
import logging

from charms.nginx_ingress_integrator.v0.ingress import IngressRequires
from ops.charm import CharmBase, ConfigChangedEvent, PebbleReadyEvent
from ops.main import main
from ops.model import ActiveStatus, BlockedStatus, WaitingStatus

logger = logging.getLogger(__name__)

ATLANTIS_PORT = 4141


class AtlantisOperatorCharm(CharmBase):
    """Charm for Atlantis on kubernetes."""

    def __init__(self, *args):
        """Init function for the charm.

        Args:
            args: Variable list of positional arguments passed to the parent constructor.
        """
        super().__init__(*args)
        self.framework.observe(self.on.atlantis_pebble_ready, self._on_atlantis_pebble_ready)
        self.framework.observe(self.on.config_changed, self._on_config_changed)

        self.ingress = IngressRequires(
            self,
            {
                "service-hostname": self._ingress_hostname,
                "service-name": self.app.name,
                "service-port": ATLANTIS_PORT,
            },
        )

    #########################################################################
    # Juju event handlers
    #########################################################################

    def _on_atlantis_pebble_ready(self, event: PebbleReadyEvent) -> None:
        """Handle atlantis_pebble_ready event and configure workload container.

        Args:
            event: Event triggering the pebble ready hook for the atlantis container.
        """
        required_config = self._required_config()
        if required_config:
            missing_config = ", ".join(required_config)
            self.unit.status = BlockedStatus(f"Missing required config: {missing_config}")
            return
        # Get a reference the container attribute on the PebbleReadyEvent
        container = event.workload
        # Add initial Pebble config layer using the Pebble API
        container.add_layer("atlantis", self._pebble_layer, combine=True)
        # Make Pebble reevaluate its plan, ensuring any services are started if enabled.
        container.replan()
        # Mark status active.
        self.unit.status = ActiveStatus()

    def _on_config_changed(self, event: ConfigChangedEvent) -> None:
        """Handle configuration changed event.

        Args:
            event: Event indicating configuration has been changed.
        """
        # Fetch the new config value
        self.ingress.update_config({"service-hostname": self._ingress_hostname})

        required_config = self._required_config()
        if required_config:
            missing_config = ", ".join(required_config)
            self.unit.status = BlockedStatus(f"Missing required config: {missing_config}")
            return

        # The config is good, so update the configuration of the workload
        container = self.unit.get_container("atlantis")
        # Verify that we can connect to the Pebble API in the workload container
        if container.can_connect():
            # Push an updated layer with the new config
            container.add_layer("atlantis", self._pebble_layer, combine=True)
            container.replan()

            self.unit.status = ActiveStatus()
        else:
            # We were unable to connect to the Pebble API, so we defer this event
            event.defer()
            self.unit.status = WaitingStatus("waiting for Pebble API")

    #########################################################################
    # Charm-specific functions and properties
    #########################################################################

    @property
    def _site_name(self) -> str:
        """Get the site_name property.

        Defaults to deployed application name if not specified via juju config.

        Returns:
            The site name as a string.
        """
        return self.config["site-name"] or f'http://{self.app.name}'

    @property
    def _ingress_hostname(self) -> str:
        """Get the ingress hostname.

        This strips the URL scheme from self._site_name.

        Returns:
            The ingress hostname to use as a string.
        """
        return "".join(self._site_name.split("://")[1:])

    def _required_config(self) -> list[str]:
        """Return a list of required config items that aren't set.

        Returns:
            A list of strings of the juju config options that are required but
            not specified.
        """
        required_config = [
            "gh-token",
            "gh-user",
            "repo-allowlist",
            "webhook-secret",
        ]
        return [x for x in required_config if not self.config[x]]

    def _env_variables(self) -> dict:
        """Assemble the environment variables that should be passed to Atlantis.

        Returns:
            A dictionary of environment variables to be passed to Atlantis.
        """
        environment = {
            "ATLANTIS_ATLANTIS_URL": self._site_name,
            "ATLANTIS_GH_USER": self.config["gh-user"],
            "ATLANTIS_GH_TOKEN": self.config["gh-token"],
            "ATLANTIS_GH_WEBHOOK_SECRET": self.config["webhook-secret"],
            "ATLANTIS_REPO_ALLOWLIST": self.config["repo-allowlist"],
        }
        if self.config["additional-env-variables"]:
            # XXX: We should do some validation here.
            environment.update(json.loads(self.config["additional-env-variables"]))
        return environment

    @property
    def _pebble_layer(self) -> dict:
        """Return a dictionary representing a Pebble layer.

        Returns:
            A dictionary representing the Pebbel layer for Atlantis.
        """
        # We need to pass the --port variable to 'atlantis server` because
        # otherwise it's looking for an environment variable of ATLANTIS_PORT
        # which is set by Juju/K8s based on the pod configuration to
        # 'tcp://${POD_IP}:65535'.
        return {
            "summary": "atlantis layer",
            "description": "pebble config layer for atlantis",
            "services": {
                "atlantis": {
                    "override": "replace",
                    "summary": "atlantis",
                    "command": f"atlantis server --port={ATLANTIS_PORT}",
                    "startup": "enabled",
                    "environment": self._env_variables(),
                }
            },
            "checks": {
                "atlantis-ready": {
                    "override": "replace",
                    "level": "ready",
                    "tcp": {"port": ATLANTIS_PORT},
                }
            },
        }


if __name__ == "__main__":  # pragma: nocover
    main(AtlantisOperatorCharm)
