# atlantis-operator

Currently this operator only supports GitHub. Support for GitLab, Bitbucket and Azure DevOps could be added in the
future based on user requests.

To run this locally:

    charmcraft pack
    juju deploy ./atlantis_ubuntu-22.04-amd64.charm --resource atlantis-image='ghcr.io/runatlantis/atlantis'

You'll need to provide the following config options:

* gh-user
* gh-token
* webhook-secret
* repo-allowlist
