#!/bin/bash


export PYTHONPATH=.


nohup python web/main_service.py &

python web/pm_check_queue.py &>/dev/null &
python web/pm_auto_create_queue.py &>/dev/null &
python web/pm_man_create_queue.py &>/dev/null &
