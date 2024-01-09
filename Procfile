bot: python -m ebmbot.bot
dispatcher: python -m ebmbot.dispatcher
web: gunicorn --config /app/gunicorn/conf.py ebmbot.webserver:app
release: rm -f /storage/.bot_startup_check
