from fabric.api import abort, env, prefix, run, task
from fabric.context_managers import cd
from fabric.contrib.files import exists

env.forward_agent = True
env.colorize_errors = True

env.hosts = ["smallweb1.ebmdatalab.net"]
env.user = "root"
env.path = "/var/www/ebmbot"


def make_directory():
    run(f"mkdir -p {env.path}")


def check_environment():
    environment_path = "{env.path}/environment"

    if not exists(environment_path):
        abort(f"Create {environment_path} before proceeding")


def create_venv():
    if not exists(f"venv"):
        run(f"python3.8 -m venv venv")


def update_from_git():
    if not exists(f".git"):
        run(f"git clone -q git@github.com:ebmdatalab/ebmbot.git")

    run(f"git fetch --all")
    run(f"git checkout --force origin/master")


def install_requirements():
    with prefix(f"source venv/bin/activate"):
        run(f"pip install -q -r requirements.txt")


def chown_everything():
    run(f"chown -R ebmbot:ebmbot {env.path}")


def set_up_systemd():
    for service in ["bot", "webserver", "dispatcher"]:
        run(
            "ln -sf {env.path}/deploy/systemd/app.ebmbot.{service}.service /etc/systemd/system"
        )
        run(f"sudo systemctl enable app.ebmbot.{service}.service")

    run(f"systemctl daemon-reload")


def restart_ebmbot():
    for service in ["bot", "webserver", "dispatcher"]:
        run(f"systemctl restart app.ebmbot.{service}.service")


@task
def deploy():
    make_directory()
    check_environment()

    with cd(env.path):
        create_venv()
        update_from_git()
        install_requirements()
        chown_everything()
        set_up_systemd()
        restart_ebmbot()
