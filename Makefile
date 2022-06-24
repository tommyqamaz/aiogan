BOT_PATH=bot/bot.py

run:
	poetry run python $(BOT_PATH)

clean:
	rm -r */__pycache__

getpwd:
	env pwd && ls