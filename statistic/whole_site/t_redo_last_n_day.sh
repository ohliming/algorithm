#!/bin/bash

cd  `dirname $0`
pwd

num=$1
echo $num
for i in `seq $num |sort -rn`;do
  echo $i
  yesday=`date -d -${i}day +"%Y%m%d"`
  yesday2=`date -d -${i}day +"%Y-%m-%d"`
  echo $yesday
  sh redo.sh $yesday
done

