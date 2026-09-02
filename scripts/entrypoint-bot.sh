#!/bin/sh
set -e
echo "Starting Telegram bot (polling)..."
exec python -m app.bot.main
