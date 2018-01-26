cd `dirname $0`
path=`pwd`
today=`date "+%Y%m"`
log=${path}/log/batch_update.log

if [ ! -d "${path}/log" ];then
  mkdir ${path}/log
fi

ctime=`date "+%Y-%m-%d %H:%M:%S"`
echo "[INFO] [$ctime] start scan online company" >> ${log}
nohup python ./recommend.py  1>>${log} 2>&1
