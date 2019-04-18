#!/usr/bin/env bash
current_path=`pwd`
path="/home/hjd/PycharmProjects/seekplum/term"
cmd="python main.py"
source /home/hjd/seekplum-env/bin/activate > /dev/null
cd $path

var=" "
for i
do
    var+=" $i"
done

$cmd $var
cd $current_path
