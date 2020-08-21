THIS_FILE := $(lastword $(MAKEFILE_LIST))
.PHONY: build-up rebuild rebuild-up build up start down destroy stop restart logs status prune bash psql test

################## Manage docker-compose.yml file
build:
	docker-compose -f docker-compose.yml build $(container)

rebuild:
	docker-compose -f docker-compose.yml build --no-cache $(container)

up:
	docker-compose -f docker-compose.yml up -d $(container)

build-up: build up

rebuild-up: rebuild up

start:
	docker-compose -f docker-compose.yml start $(container)

down:
	docker-compose -f docker-compose.yml down $(container)

destroy:
	docker-compose -f docker-compose.yml down -v $(container)

stop:
	docker-compose -f docker-compose.yml stop $(container)

restart: stop up

logs:
	docker-compose -f docker-compose.yml logs --tail=100 -f $(container)

status:
	docker-compose -f docker-compose.yml ps

prune:
	# clean all that is not used
	docker prune -af

# Interact with docker-compose.yml container
bash:
	docker-compose -f docker-compose.yml exec $(container) /bin/bash

psql:
	docker-compose -f docker-compose.yml exec $(container) psql -U postgres

test:
	# here it is useful to add your own customised tests
	docker-compose -f docker-compose.yml exec $(container) /bin/bash -c '\
		echo "Hello !" && echo "Docker runs!"' \
	&& echo success


################## Conda
conda_env_list:
	conda info --envs

conda_pkg_list:
	conda list

conda_create_env:
	conda create -y --name $(env_name) python=$(py_vers)

conda_clone_env:
	conda create -y --clone $(from) --name $(to)

conda_rmv_env:
	conda env remove -n $(env_name)

conda_env_from_yml:
	conda env create -y -f environment.yml

conda_export_env:
	conda env export > environment.yml

conda_env_from_reqs:
	conda install --yes --file requirements.txt

export_reqs:
	conda list -e export > requirements.txt

conda_add_channel:
	conda config --add channels $(channel_name)

conda_package_docker:
	docker build -f pkg.Dockerfile -t conda_package .
	docker run -it conda_package

conda_build_runner:
	chmod -rw conda_build_runner.sh
	bash conda_build_runner.sh


################## Python tests
pytest-cov:
	python -m pytest --cov=$(lib_dir) tests/

pytest:
	python -m pytest tests/


################## Python
black:
	black *.py

################## Git
git_pre-commit:
	# to install git hooks in your .git/ directory
	pre-commit install
