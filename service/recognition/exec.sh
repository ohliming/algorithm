#!/bin/sh
# train model 
python crf_model.py ./train/ train.data learn
./bin/crf_learn -c 5.0 template train.data model

# test 
python crf_model.py ./test/ test.data tag
./bin/crf_test  -m model test.data > result.txt

# get company entity
python recognition.py
mv ./test/* ./train/ 
