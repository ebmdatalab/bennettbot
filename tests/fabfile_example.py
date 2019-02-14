from fabric.api import run
from fabric.api import abort
from fabric.api import env

env.user = None
env.hosts = ['localhost']
env.forward_agent = True
env.colorize_errors = False
env.disable_known_hosts = True


def do_run():
    return run('echo "hello world"')


def do_disallowed_thing():
    return run('cat /etc/sudoers')


def do_abort():
    abort("some error")
