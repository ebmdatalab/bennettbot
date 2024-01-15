bot: python -m ebmbot.bot
dispatcher: sh -c 'eval `ssh-agent` && ssh-add ~/.ssh/id_ed25519 && python -m ebmbot.dispatcher'
web: gunicorn --config /app/gunicorn/conf.py ebmbot.webserver:app
release: rm -f /storage/.bot_startup_check
