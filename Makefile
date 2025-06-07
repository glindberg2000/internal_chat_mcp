# Makefile for internal_chat_mcp

.PHONY: install upgrade test

install:
	pip install --force-reinstall --no-cache-dir .

upgrade:
	git pull origin main
	pip install --force-reinstall --no-cache-dir .

tag:
	git fetch --tags
	git checkout v0.2.4
	pip install --force-reinstall --no-cache-dir .

test:
	python test_get_unread_messages.py 