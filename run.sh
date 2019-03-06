#!/bin/sh
python -u facex_group_search_zyf.py \
    --api-names remove_gallery+create_gallery+add_face+search \
    --gallery-list ./gallery_haixin_lfw_final_new.txt \
    --probe-list  ./probe_haixin_lfw_final_new.txt \
    --threshold 0.40 \
    --top 6 \
    --gallery-id 0 \
    --save-dir ./haixin_0.4_1vN_results \
    --config ./facex_api_config_v2_argus.json > haixin_lfw_thresh_0.4.log
    
