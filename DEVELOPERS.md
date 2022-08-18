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
just dev_setup
```

### Set up a test slack workspace and app

Create a [new slack workspace](https://slack.com/intl/en-gb/get-started#/createnew) to use for testing.

Follow the steps to [create a slack app with the required scopes](DEPLOY.md#creating-the-slack-app)
and install it into your test workspace.

### Set up environment
* Copy environment: `cp environment-sample environment`

Edit `environment` with the slack app tokens etc for the test slack app.


### Run checks

Run linter and formatted:
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
