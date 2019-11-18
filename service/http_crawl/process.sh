echo '---process start ---' # start

mysql -h47.106.168.190 -uroot -palkf@xpdw -Dduyi_core -e "delete from crawl_css"
python crawl_css.py & # process css
if [ $? -eq 0 ];then
echo "css 抓取执行成功"
else
echo "css 抓取执行出错"
fi

mysql -h47.106.168.190 -uroot -palkf@xpdw -Dduyi_core -e "delete from crawl_jquery"
python crawl_jquery.py # process jquery
if [ $? -eq 0 ];then
echo "jquery 抓取执行成功"
else
echo "jquery 抓取执行出错"
fi

mysql -h47.106.168.190 -uroot -palkf@xpdw -Dduyi_core -e "delete from crawl_html"
python crawl_html.py # process html
if [ $? -eq 0 ];then
echo "html 抓取执行成功"
else
echo "html 抓取执行出错"
fi

mysql -h47.106.168.190 -uroot -palkf@xpdw -Dduyi_core -e "delete from crawl_js"
python crawl_js.py # process html
if [ $? -eq 0 ];then
echo "html 抓取执行成功"
else
echo "html 抓取执行出错"
fi

echo '---process done---' # end 