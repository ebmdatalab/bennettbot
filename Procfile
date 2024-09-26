bot: python -m bennettbot.bot
dispatcher: sh -c 'eval `ssh-agent` && ssh-add ~/.ssh/id_ed25519 && python -m bennettbot.dispatcher'
web: gunicorn --config /app/gunicorn/conf.py bennettbot.webserver:app
release: rm -f /storage/.bot_startup_check
