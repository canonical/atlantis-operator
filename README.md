# atlantis-operator

This charm is still under active development.

Currently this operator only supports GitHub. Support for GitLab, Bitbucket and Azure DevOps could be added in the
future based on user requests.

To deploy from charmhub:

    juju deploy atlantis --channel=edge

To run this locally:

    charmcraft pack
    juju deploy ./atlantis_ubuntu-22.04-amd64.charm --resource atlantis-image='ghcr.io/runatlantis/atlantis'

You'll need to provide the following config options:

* gh-user
* gh-token
* webhook-secret
* repo-allowlist

For ingress, the charm supports the nginx-route integration, provided by the nginx-ingress-integrator charm:

    juju deploy nginx-ingress-integrator --trust --config service-hostname=atlantis.local --config path-routes=/
    juju integrate nginx-ingress-integrator atlantis
