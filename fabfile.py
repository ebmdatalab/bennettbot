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
    environment_path = f"{env.path}/.env"

    if not exists(environment_path):
        abort(f"Create {environment_path} before proceeding")


def create_venv():
    if not exists("venv"):
        run("python3.8 -m venv venv")


def update_from_git():
    if not exists(".git"):
        run("git clone -q git@github.com:ebmdatalab/ebmbot.git")

    run("git fetch --all")
    run("git checkout --force origin/master")


def install_requirements():
    with prefix("source venv/bin/activate"):
        run("pip install -q -r requirements.prod.txt")


def chown_everything():
    run(f"chown -R ebmbot:ebmbot {env.path}")


def set_up_systemd():
    for service in ["bot", "webserver", "dispatcher"]:
        run(
            f"ln -sf {env.path}/deploy/systemd/app.ebmbot.{service}.service /etc/systemd/system"
        )
        run(f"sudo systemctl enable app.ebmbot.{service}.service")

    run("systemctl daemon-reload")


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
