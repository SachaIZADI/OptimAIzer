.DEFAULT_GOAL := help
PYTHON_VERSION := $(shell cat .python-version)
ENV_VARS := $(shell cat .env | xargs)


.PHONY: install-python
install-python: ## Install the specified Python version
	@if [ -n "$$(pyenv versions | grep $(PYTHON_VERSION))" ]; then \
	  echo "Requirement Python $(PYTHON_VERSION): already installed."; \
	else \
	  pyenv install $(PYTHON_VERSION) && \
	  pyenv local $(PYTHON_VERSION) && \
	  echo "Requirement Python $(PYTHON_VERSION): installed."; \
	fi

PYTHON_PATH := $(shell pyenv which python $(PYTHON_VERSION))

.PHONY: setup
setup: install-python ## Setup the project for the first time
	poetry env use $(PYTHON_PATH) && poetry install
	poetry run pre-commit install

.PHONY: pre-commit
pre-commit: ## Run pre-commit
	poetry run pre-commit run --all-files

.PHONY: start-chat
start-chat: ## Start the chat app
	( sleep 3 && open http://localhost:32123 ) & \
	poetry run mesop optimaizer/app.py
