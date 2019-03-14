This is a Python [slackbot](https://github.com/lins05/slackbot). To start it:

    python ebmbot_runner.py

On a live server, it's managed by `supervisord`.

The bot does deployment-related actions by **executing fabric tasks**.
Fabric is used for historic reasons - it's the system we already used
for deployment.

Note that one unfortunate consequence of this is that none of these
tasks are thread-safe: fabric maintains state in a module global
called `env` which is shared between all fabric tasks; and bot
commands are executed in threads.  In practice this is unlikely to be
a big issue due to how rarely we run commands.

The use of fabric requires two things:

1. Fabfiles for each repo, which are vendored to be local to the bot (in `fabfiles/`)
  * These are listed in `fabfiles.json`; run `get_fabfiles.py` to fetch these and minimally sanity check dependencies; that is also run during a deploy as a sanity check that everything is up-to-date
2. The user that this bot runs as must have passwordless ssh access to the live server
3. That same user on the live server must have passwordless `sudo` access to any scripts that will run with escalated privileges. By convention, these live in each repository in `deploy/fabric_scripts/` in each project. We accomplish this via membership of a group called `fabric` and the appropriate `sudoer` configuration
  * Test with something like `sudo -u ebmbot ssh <host> sudo /var/www/somepath/deploy/fab_scripts/hello.sh`
4. Therefore, fabric commands that require root must use a modified `sudo` method (specifically, `run("sudo <cmd>")` rather than `sudo(<cmd>)`.  See [here](https://github.com/ebmdatalab/openprescribing/blob/01871a2fe5c9ca5acffd664e52735c847451bcf2/fabfile.py#L39-L55) for an example
