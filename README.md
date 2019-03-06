# FACEX 1比N检索API测试

## 0. 安装依赖文件
```cmd
pip install requests
```

## 1.  修改服务配置json文件
1. 复制facex_api_config_tmpl.json，并重命名为facex_api_config.json
2. 替换<service_host_url>为对应的服务主机url或者IP,例如http://ava-argus-gate.xs.cg.dora-internal.qiniu.io:5001 或者127.0.0.1:5001，端口要跟具体服务对应的端口一致。
3. 根据需要修改url_prefix, 如果gallery_list和probe_list中的文件url都是完整的url（以http开头），则该字段可以为空。

```
    "facx_gallery":"1",  # 人脸库id，需要与创建，移除，增加部分一致
    "search_threshold":"0.4", # 人脸检索阈值
    "search_top_n":"5",  # 输出大于阈值的前6（若有）匹配人脸信息
    "register_mode": "LARGEST", # 若入库图片中检测到多个人脸，取面积最大的人脸入库

    "facex_remove_gallery":"<service_host_url>/v1/face/group/1/remove", # api路径，清空id=1人脸库
    "facex_create_gallery": "<service_host_url>/v1/face/group/1/new", # api路径，创建id=1人脸库
    "facex_add_face":       "<service_host_url>/v1/face/group/1/add", # api路径，填加人脸到id=1人脸库
    "facex_search":"<service_host_url>/v1/face/groups/search", # api检索路径
    "url_prefix": "http://p6yobdq7s.bkt.clouddn.com", #url prefix
```

## 2.  准备入库列表和查询列表
1. 新建两个列表文件：入库列表gallery_list.txt和查询列表probe_list.txt；

2. 将入库和测试图像的url和name_id （身份标识符）分别放到gallery_list.txt和probe_list.txt，格式示例为:

    ```
    http://xxx/xxx/1.jpg jack
    http://xxx/xxx/2.jpg rose
    http://xxx/xxx/3.jpg unkown
    ...
    ```

3. gallery_list.txt的每行必须要有name_id，probe_list.txt的name_id可以缺省，缺省即默认probe图片不在底库当中。

## 3. 执行测试脚本
修改run.sh (Linux/MacOs) 或者run.bat 中的参数，并执行。

或者直接执行
```cmd
python facex_group_search_zyf.py ...
```

```cmd
usage: facex_group_search_zyf.py [-h] [--api-names API_NAMES]
                                 [--config CONFIG_FILE]
                                 [--gallery-id GALLERY_ID]
                                 [--gallery-list GALLERY_LIST_FILE]
                                 [--probe-list PROBE_LIST_FILE]
                                 [--threshold THRESHOLD] [--top TOP_N]
                                 [--save-dir SAVE_DIR]FaceX Search API test

optional arguments:
  -h, --help            show this help message and exit
  --api-names API_NAMES
                        APIs to test, choose one or a combination seperated by
                        "+" from:['add_face', 'search', 'create_gallery',
                        'remove_gallery']
  --config CONFIG_FILE  path to config json file, which sets API URLs
  --gallery-id GALLERY_ID
                        string, default="1", the gallery id you want to create
                        or search
  --gallery-list GALLERY_LIST_FILE
                        path to gallery list file, each line of which is
                        "<url> <name_id>"
  --probe-list PROBE_LIST_FILE
                        path to probe list file, each line of which is "<url>
                        <name_id>"
  --threshold THRESHOLD
                        threshold for facex search api
  --top TOP_N           top_N for facex search api
  --save-dir SAVE_DIR   directory to save output results, default: 1vN-results
                        [-<TIME-STAMP>]
```

## 4. 输出结果说明
执行脚本后输出结果存在<save-dir>路径下面，统计信息在<save-dir>/1vN_result.txt，该文件中记录入库成功率以及查询时top-N的召回率、漏检率、误报率、命中精度。

```
入库成功率：
	register_suc_rate = 成功入库的图像个数 / 尝试入库的图像个数 * 100%

召回率(命中率)：
     recall_rate =  确实在底库中且返回匹配命中的图像个数 / 确实在底库中的测试图像总数 * 100%

漏报率：
    miss_rate = 100% - recall_rate

误报率：
    FPR (false positive rate) =  确实不在底库中但返回有匹配命中的图像个数 / 确实不在底库中的测试图像总数 * 100%

命中精度：
    precision =  确实在底库中且匹配命中的图像个数 / ( 确实在底库中且返回匹配命中的图像个数 + 确实不在底库中但返回有匹配命中的图像个数) * 100%
```

返回示例：
```
===================
register_suc_cnt = 7
gallery_list_cnt = 10
register_suc_rate = 70%


===================
probe_cnt = 20
probe_failed_cnt = 6
pos_probe_cnt = 5
neg_probe_cnt = 9
pos_probe_topN_suc_cnt_list = [5, 5, 5, 5, 5, 5]
neg_probe_topN_fail_cnt_list = [0, 0, 0, 0, 0, 0]

===================

===================
---> Top 1: 
    recall rate = 100%
    miss rate = 0%
    precision = 100%
    false positive reate = 0%

===================
---> Top 2: 
    recall rate = 100%
    miss rate = 0%
    precision = 100%
    false positive reate = 0%

===================
---> Top 3: 
    recall rate = 100%
    miss rate = 0%
    precision = 100%
    false positive reate = 0%

===================
---> Top 4: 
    recall rate = 100%
    miss rate = 0%
    precision = 100%
    false positive reate = 0%

===================
---> Top 5: 
    recall rate = 100%
    miss rate = 0%
    precision = 100%
    false positive reate = 0%

===================
---> Top 6: 
    recall rate = 100%
    miss rate = 0%
    precision = 100%
    false positive reate = 0%

```# face1n-demo
