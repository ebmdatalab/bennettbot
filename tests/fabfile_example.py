from fabric.api import run
from fabric.api import abort
from fabric.api import env
from fabric.context_managers import prefix

env.user = None
env.hosts = ['localhost']
env.forward_agent = True
env.colorize_errors = False
env.disable_known_hosts = True


def _remove_job_stages():
    # A hack to address the fact that our Travis environment is not
    # passed to the ssh subshell.
    #
    # Discussion of the issue here:
    # https://travis-ci.community/t/travis-functions-no-such-file-or-directory/2286/2
    run('if [ -f /home/travis/.travis/job_stages ];'
        '  then echo "#!/bin/bash" > /home/travis/.travis/job_stages;'
        'fi')


def do_run():
    _remove_job_stages()
    return run('echo "hello world"')


def do_disallowed_thing():
    _remove_job_stages()
    return run('cat /etc/sudoers')


def do_abort():
    abort("some error")
