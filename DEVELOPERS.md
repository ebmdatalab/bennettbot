# Notes for developers

## System requirements

### just

Follow the installation instructions from the [Just Programmer's Manual](Follow [installation instructions](https://just.systems/man/en/chapter_4.html) for your OS.

#### Add completion for your shell. E.g. for bash:
```
source <(just --completions bash)
```

#### Show all available commands
```
just #  shortcut for just --list
```

### shellcheck
```sh
# macOS
brew install shellcheck

# Linux
apt install shellcheck
```


## Local development environment

Set up your local .env file by running

```
./scripts/local-setup-sh
```

This will create a `.env` file by copying `dotenv-sample`, and will use the
Bitwarden CLI to retrieve relevant dev secrets and update environment variables and credentials.

By default, re-running the script will skip updating secrets from Bitwarden
if they are already populated. To force them to update again:

```
./scripts/local-setup-sh -f
```

### bitwarden CLI

If you don't have the Bitwarden CLI already installed, the `local-setup.sh`
will prompt you to [install it](https://bitwarden.com/help/cli/#download-and-install).


### Join the test slack workspace

Join the test Slack workspace at [bennetttest.slack.com](https://bennetttest.slack.com).

The test slack bot's is already installed to this workspace.  Its username is
`bennett_test_bot` and, when you are running the bot locally, you can
interact with it by using `@Bennett Test Bot`.

Alternatively, you can [create your own new slack workspace](https://slack.com/get-started#/createnew) to use for testing, and follow the instructions in the [deployment docs](DEPLOY.md) to create a new test slack app, generate tokens
and install it to the workspace. You will need to update your `.env` file with
the relevant environment variables.

## Run locally

### Run checks

Run linter, formatter and shellcheck:
```
just check
```

Fix issues:
```
just fix
```

### Tests
Run the tests with:
```
just test <args>
```

### Run individual services:
```
just run <service>
```

To run the slack bot and use it to run jobs, run both the bot and dispatcher:
```
just run bot
just run dispatcher
```

## Run in docker

### Update environment

Update the following environment variables in your .env file
(defaults for docker are included in `dotenv-sample`)
GCP_CREDENTIALS_PATH="/app/writeable_dir/gcp-credentials.json"
LOGS_DIR="/app/logs"
WRITEABLE_DIR="/app/writeable_dir"

### Build docker image

This builds the dev image by default:

```
just docker/build
```

### Run checks

```
just docker/check`
```

### Run tests
```
just docker/test
```

### Run all services

Run all 3 services (bot, dispatcher and webserver) in separate docker
containers.

```
just docker/run-all
```

### Restart all services

Restart all running services.

```
just docker/restart
```

### Stop/remove containers

Stop running service container:

```
just docker/stop-all
```

Stop running services and remove containers:

```
just docker/rm-all
```
