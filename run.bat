python facex_group_search_zyf.py ^
    --api-names remove_gallery+create_gallery+add_face+search ^
    --gallery-list ./gallery_10.txt ^
    --probe-list ./probe_20.txt ^
    --threshold 0.4 ^
    --top 6 ^
    --gallery-id 1 ^
    --save-dir ./1vN_results ^
    --config ./facex_api_config_v2_argus.json
    