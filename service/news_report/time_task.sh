python update_36kr.py
python update_com.py

to=liming@36kr.com,cuiyan@36kr.com
today=`date -d -1days "+%Y%m%d"`
subject="[媒体新闻流监控-$today]"
cont=`python monitor.py`
python /usr/bin/sendmail.py --subject="$subject" --body="$cont" --to="$to" --content-type="html" --from-name="internal"
