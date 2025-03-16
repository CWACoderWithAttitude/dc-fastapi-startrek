#!/bin/sh
# pre_checkin.sh

pip install flake8 pytest pytest-cov #-r requirements.txt
#flake8 . --count --show-source --statistics
pytest test*.py --doctest-modules --junitxml=junit/test-results.xml --cov=. --cov-report=xml --cov-report=html
