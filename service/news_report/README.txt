# 更新媒体新闻说明文档
# 假设安装路径 path : /data/work/data_servers/prod-algorithm-media/service/news_report

#####################################
40 * * * * cd /data/work/data_servers/prod-algorithm-media/service/news_report && python fetch_url.py
30 00 * * * cd /data/work/data_servers/prod-algorithm-media/service/news_report && sh time_task.sh
#####################################

