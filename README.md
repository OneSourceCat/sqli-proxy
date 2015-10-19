# sqli-proxy
##0x00 介绍
sqli-proxy使用了sqlmapapi和基于tornado实现的http-proxy来探测上网的流量中是否存在SQL注入。
sqli-proxy暂时不提供Web UI。
##0x01 配置
创建本地数据库sqli，相关数据库配置在`config.py`文件中,分别对sqlmapapi的server和数据进行配置，默认配置如下：
```
# sqlmapapi server config
SERVER = 'http://127.0.0.1:8775'

# database config
host = '127.0.0.1' 
user = 'root' 
password = ''
db_name = 'sqli'
port = 3306
charset = 'utf8'
```
需要安装tornado，requests等第三方python库：
```
pip install tornado
pip install requests
...
```
在`blacklist.txt`配置忽略域名，每行一个，不允许存在空行：
```
www.baidu.com
www.qq.com
www.sina.cn
www.163.com
```
##0x02 运行
1、运行sqlmapapi和proxy.py即可：
```
python sqlmapapi.py -s
python proxy.py 8080 baidu.com
```
python proxy.py [proxy-port] [detecting-domain]
默认端口为8080，domain为空。

2、设置浏览器代理为：
```
127.0.0.1:[8080/你配置过的端口]
```
##0x03 结果
结果保存在sqli数据库中的sqlirecords表中，分为url和request_body。
