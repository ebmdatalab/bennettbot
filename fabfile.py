from fabric.api import abort, env, prefix, run, sudo, task
from fabric.context_managers import cd
from fabric.contrib.files import exists

env.forward_agent = True
env.colorize_errors = True

env.hosts = ["smallweb1.ebmdatalab.net"]
env.user = "ebmbot"
env.path = "/var/www/ebmbot2"  # TODO change this, and also in the service files


def make_directory():
    run("mkdir -p {}".format(env.path))


def check_environment():
    environment_path = "{}/environment".format(env.path)

    if not exists(environment_path):
        abort("Create {} before proceeding".format(environment_path))


def create_venv():
    if not exists("venv"):
        run("python3.5 -m venv venv")


def update_from_git():
    if not exists(".git"):
        run("git clone -q git@github.com:ebmdatalab/ebmbot.git")

    run("git fetch --all")
    run("git checkout --force origin/ebmbot2")  # TODO change this


def install_requirements():
    with prefix("source venv/bin/activate"):
        run("pip install -q -r requirements.txt")


def set_up_systemd():
    for service in ["bot", "webserver", "dispatcher"]:
        sudo(
            "ln -sf {}/deploy/systemd/app.ebmbot.{}.service /etc/systemd/system".format(
                env.path, service
            )
        )

    sudo("sudo systemctl daemon-reload")


def restart_ebmbot():
    for service in ["bot", "webserver", "dispatcher"]:
        sudo("sudo systemctl restart app.ebmbot.{}.service".format(service))


@task
def deploy():
    make_directory()
    check_environment()

    with cd(env.path):
        create_venv()
        update_from_git()
        install_requirements()
        set_up_systemd()
        restart_ebmbot()
