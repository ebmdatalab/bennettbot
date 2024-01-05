# Notes for developers

## System requirements

### just

```sh
# macOS
brew install just

# Linux
# Install from https://github.com/casey/just/releases

# Add completion for your shell. E.g. for bash:
source <(just --completions bash)

# Show all available commands
just #  shortcut for just --list
```


## Local development environment


Set up a local development environment with:
```
just devenv
```

This will create a virtual environment, install requurements and create a
`.env` file by copying `dotenv-sample`; update it as necessary with valid dev
values for environment variables.


### Set up a test slack workspace and app

Create a [new slack workspace](https://slack.com/intl/en-gb/get-started#/createnew) to use for testing.

Follow the steps to [create a slack app with the required scopes](DEPLOY.md#creating-the-slack-app)
and install it into your test workspace.


### Set up environment

Edit `.env` with the slack app tokens etc for the test slack app.


## Run in docker

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

### Stop/remove containers

Stop running service container:

```
just docker/stop-all
```

Stop running services and remove containers:

```
just docker/rm-all
```

## Run locally

### Run checks

Run linter and formatter:
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

To run the slack bot and test jobs, run both the bot and dispatcher:
```
just run bot
just run dispatcher
```
