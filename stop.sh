#!/bin/bash


export PYTHONPATH=.


for i in main_service.py pm_check_queue.py pm_auto_create_queue.py pm_man_create_queue.py
do
    ps -ef |grep $i |grep -v grep |awk '{print $2}' |xargs sudo kill
done
