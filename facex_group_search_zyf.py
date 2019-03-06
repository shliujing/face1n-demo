#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: zhaoyafei@qiniu.com
"""
from __future__ import print_function

import os
import os.path as osp

import sys
import time
import json

import requests
import argparse

from ava_auth import AuthFactory


reload(sys)
sys.setdefaultencoding("utf-8")

_API_NAMES = ['add_face', 'search', 'create_gallery', 'remove_gallery']  #

RECREATE_GALLERY = True
ADD_GALLERY = True
PROBE_LARGEST = True


def parse_args():
    """Parse input arguments."""
    parser = argparse.ArgumentParser(description='FaceX Search API test')
    parser.add_argument('--api-names', dest='api_names',
                        help='APIs to test, choose one or a combination seperated by "+" from:' +
                        str(_API_NAMES),
                        default='+'.join(_API_NAMES))
    parser.add_argument('--config', dest='config_file',
                        help='path to config json file, which sets API URLs',
                        default='./facex_api_config_v3.json')
    parser.add_argument('--gallery-id', dest='gallery_id',
                        help='string, default="1", the gallery id you want to create or search',
                        type=str,
                        default='1')
    parser.add_argument('--gallery-list', dest='gallery_list_file',
                        help='path to gallery list file, each line of which is "<url> <name_id>"',
                        default='./gallery_list.txt')
    parser.add_argument('--probe-list', dest='probe_list_file',
                        help='path to probe list file, each line of which is "<url> <name_id>"',
                        default='./probe_list.txt')
    parser.add_argument('--threshold', dest='threshold',
                        help='threshold for facex search api',
                        type=float,
                        default=0.4)
    parser.add_argument('--top', dest='top_n',
                        help='top_N for facex search api',
                        type=int,
                        default=6)
    parser.add_argument('--save-dir', dest='save_dir',
                        help='directory to save output results, default: 1vN-results[-<TIME-STAMP>]',
                        default='./1vN-results')

    args = parser.parse_args()

    return args


def get_time_stamp():
    _str = time.strftime('-TS%y%m%d-%H%M%S')
    return _str


def load_config_file(config_json):
    fp = open(config_json, 'r')
    configs = json.load(fp)
    # print(configs)
    fp.close()
    return configs


def get_auth_token(configs):
    header = None
    token = None

    if 'ava_auth_conf' in configs:
        conf = configs['ava_auth_conf']
        factory = AuthFactory(conf["access_key"], conf["secret_key"])
        if conf["auth"] == "qiniu/mac":
            fauth = factory.get_qiniu_auth
        else:
            fauth = factory.get_qbox_auth

        token = fauth()
    elif 'Authorization' in configs:
        header = {"Authorization": configs['Authorization']}
    else:
        header = {"Authorization": "QiniuStub uid=1&ut=2"}

#    print 'token: ', token

    return header, token


def send_request_to_url(url, data, header=None, token=None):
    hdr = {'content-type': 'application/json'}
#    hdr={"Content-Type": "application/x-www-form-urlencoded"},
    if header:
        hdr.update(header)

    resp = None
    if isinstance(data, dict):
        req = requests.post(url, None, data, headers=hdr, auth=token)
        # print('--->req.headers: ' + str(req.headers))
#        print('--->req.content: ' + str(req.content))
        resp = req.content
    elif isinstance(data, str) and data.endswith('.json'):
        fp = open(data)
        data = json.load(fp)
        fp.close()
        req = requests.post(url, None, data, headers=hdr)
        resp = req.content

    return resp


def get_url_and_name_id(line):
    url = ''
    name_id = ''

    if not line:
        return url, name_id

    splits = line.split()
    url = splits[0]

    if len(splits) > 1:
        name_id = splits[1]
    else:
        splits2 = url.split('/')[-1]
        name_id = splits2.rsplit('_', 2)[-1]

    return url, name_id


def split_api_names(api_names):
    if isinstance(api_names, str):
        if '+' in api_names:
            api_list = api_names.split('+')
        else:
            api_list = [api_names]
    else:
        api_list = api_names

    api_names = []

    for it in api_list:
        it = it.strip()

        if it in _API_NAMES:  # and it not in api_names:
            api_names.append(it)

    return api_names


def request_facex_api(api_names,
                      gallery_list_file,
                      probe_list_file,
                      threshold=None,
                      top_n=None,
                      gallery_id=None,
                      config_file=None,
                      save_dir='./'):
    if not osp.exists(config_file):
        print("===> Error: Cannot find config_file: " + config_file)
        return

    print("===> Load configs from config_file: " + config_file)
    configs = load_config_file(config_file)
    print('===> configs: {}'.format(configs))
    if 'url_prefix' not in configs:
        print("===> Warning: 'url_prefix' not in config_file " + config_file)
        configs['url_prefix'] = ''
        return

    # token = None
    # header = {"Authorization": configs['Authorization']}
    header, token = get_auth_token(configs)

    print('\n---> token:', token)

    api_names = split_api_names(api_names)

    if len(api_names) < 0:
        print("===> Error: Wrong api_names: " + api_names)
        return

    if gallery_id is None:
        gallery_id = configs['gallery_id']

    gallery_id = str(gallery_id)

    for api in api_names:
        api_name = 'facex_%s' % api

        if api_name not in configs:
            print("===> Error: {} not in config_file: {}, continue to test next API".format(
                api_name, config_file))
            return
        else:
            configs[api_name] = configs[api_name].replace(
                '<gallery-id>', gallery_id)

    if not osp.exists(gallery_list_file):
        print("===> Error: Cannot find gallery_list_file: ", gallery_list_file)
        return

    if not osp.exists(probe_list_file):
        print("===> Error: Cannot find probe_list_file: ", probe_list_file)
        return

    if not osp.exists(save_dir):
        ts = get_time_stamp()
        save_dir += ts
        os.makedirs(save_dir)

    req_save_fps = {}
    for api in api_names:
        req_save_file = 'facex_' + api + '_req_data_jsonlist.txt'
        req_save_file = osp.join(save_dir, req_save_file)

        fp = open(req_save_file, 'w')
        # fp.write('[\n')
        req_save_fps[api] = fp

    resp_save_fps = {}
    for api in api_names:
        resp_save_file = 'facex_' + api + '_response_jsonlist.txt'
        resp_save_file = osp.join(save_dir, resp_save_file)

        fp = open(resp_save_file, 'w')
        # fp.write('[\n')
        resp_save_fps[api] = fp

    # create gallery
    if RECREATE_GALLERY:
        data_dict = {"data": []}

        # Test remove_gallery
        api = 'remove_gallery'

        if api in api_names:
            api_name = 'facex_' + api
            api_url = configs[api_name]
            print('===> Send [{}] request to: {}'.format(api_name, api_url))
            resp = send_request_to_url(
                api_url, data_dict, header, token)  # remove gallery

            # write_str = json.dumps(resp)
            write_str = resp + '\n'
            resp_save_fps[api].write(write_str)

        # Test create_gallery
        api = 'create_gallery'

        if api in api_names:
            # resp = send_request_to_url(
            #     configs['facex_create_gallery'], data_dict, header, token)
            api_name = 'facex_' + api
            api_url = configs[api_name]
            print('===> Send [{}] request to: {}'.format(api_name, api_url))
            resp = send_request_to_url(
                api_url, data_dict, header, token)  # remove gallery

            write_str = resp + '\n'
            resp_save_fps[api].write(write_str)

    # print('resp--->\n',resp)
    register_suc_cnt = 0
    gallery_list_cnt = 0

    gallery_unique_names = []

    # write to gallery
    fp_gallery_list = open(gallery_list_file, 'r')
    fp_register_suc = open(osp.join(save_dir, 'register_suc_list.txt'), 'w')

    register_mode = configs.get('register_mode', 'LARGEST')

    for line in fp_gallery_list:
        line = line.strip()
        if line.startswith('#'):
            continue

        url, name_id = get_url_and_name_id(line)

        if not url or url.startswith('#'):
            continue

        if 'url_prefix' in configs and not url.startswith('http'):
            url = configs['url_prefix'] + '/' + url
            # print('url',url)

        data_dict = {
            'data': [
                {
                    'uri': url,
                    "attribute": {
                        "id": name_id,
                        "name": name_id,
                        # "mode": "SINGLE",
                        # "mode": "LARGEST",
                        "mode": register_mode,
                        "desc": ""
                    }
                }
            ]
        }

        print("\n===> Try to register image:", url)

        gallery_list_cnt += 1

        # Test add_face
        api = 'add_face'
        if ADD_GALLERY and api in api_names:
            # resp = send_request_to_url(
            #     configs['facex_add_face'], data_dict, header, token)

            api_name = 'facex_' + api
            api_url = configs[api_name]
            print('===> Send [{}] request to: {}'.format(api_name, api_url))
            resp = send_request_to_url(
                api_url, data_dict, header, token)  # remove gallery

            resp_dict = json.loads(resp)
            resp_dict['img_url'] = url

            write_str = json.dumps(resp_dict) + '\n'
            resp_save_fps[api].write(write_str)

            # print('resp--->\n',resp)
            # resp_dict = json.loads(resp)
            # print('resp_dict--->\n',   resp_dict
            # and resp_dict['faces']['errors']==null :

            if 'bounding_box' in str(resp_dict['attributes']):
                register_suc_cnt += 1
                gallery_unique_names.append(name_id)
                fp_register_suc.write(line + '\n')
                print('register_suc_cnt=', register_suc_cnt)
        else:
            register_suc_cnt += 1
            gallery_unique_names.append(name_id)
            fp_register_suc.write(line + '\n')

            print('register_suc_cnt=', register_suc_cnt)

        if gallery_list_cnt % 50 == 0:
            fp_register_suc.flush()
            req_save_fps[api].flush()

    fp_gallery_list.close()
    fp_register_suc.close()

    print('************')
    print('gallery_list_cnt=', gallery_list_cnt)
    print('register_suc_cnt=', register_suc_cnt)
    print('************')

    gallery_unique_names = set(gallery_unique_names)
    print("===> {} unique names in gallery".format(len(gallery_unique_names)))

    if gallery_list_cnt < 1:
        print("===> Error: No valid gallery image url, exit...")
        exit()

    if "search" not in api_names:
        print("===> No 'search' in api_names, will not do face search, exit...")
        exit()

    # search
    probe_cnt = 0
    probe_failed_cnt = 0

    pos_probe_cnt = 0
    neg_probe_cnt = 0

    # threshold = configs['search_threshold']
    # top_n = int(configs['search_top_n'])

    if top_n < 5:
        top_n = 5

    pos_probe_topN_suc_cnt_list = []
    neg_probe_topN_fail_cnt_list = []

    for idx in range(top_n):
        pos_probe_topN_suc_cnt_list.append(0)
        neg_probe_topN_fail_cnt_list.append(0)

    print('gallery_id=', gallery_id)
    print('threshold=', threshold)
    print('top_n=', top_n)

    fp_probe_list = open(probe_list_file)
    fp_probe_suc = open(osp.join(save_dir, 'probe_suc_list.txt'), 'w')

    api = 'search'
    api_name = 'facex_' + api
    api_url = configs[api_name]

    for line in fp_probe_list:
        line = line.strip()
        if line.startswith('#'):
            continue

        url, name_id = get_url_and_name_id(line)

        if not url or url.startswith('#'):
            continue

        if 'url_prefix' in configs and not url.startswith('http'):
            url = configs['url_prefix'] + '/' + url

        probe_cnt += 1

        print("\n===> Try to probe with image: {}".format(url))
        print("    name_id=", name_id)
        print("    probe count:", probe_cnt)

        data_dict = {
            'data': {'uri': url},
            "params": {
                "groups": [gallery_id],
                "limit": int(top_n),
                "threshold": float(threshold)
            }
        }

        # resp = send_request_to_url(
        #     configs[api_name], data_dict, header, token)
        print('===> Send [{}] request to: {}'.format(api_name, api_url))
        resp = send_request_to_url(
            api_url, data_dict, header, token)  # remove gallery

        resp_dict = json.loads(resp)

        resp_dict['img_url'] = url

        write_str = json.dumps(resp_dict) + '\n'
        resp_save_fps[api].write(write_str)


        if "code" not in resp_dict:
            print("response is null,continue to next...")
            probe_failed_cnt += 1
            continue

        if resp_dict["code"] != 0:
            print('search error,code:{}'.format(resp_dict["code"]))
            probe_failed_cnt += 1
            continue

        # print('resp_dict--->\n', resp_dict
        if "faces" in resp_dict["result"]:
            detected_faces = resp_dict["result"]["faces"]
            n_detected_faces = len(detected_faces)

            print('n_detected_faces=', n_detected_faces)
            # print('matched resp-->\n',resp_dict["result"]["faces"])

            if not PROBE_LARGEST and n_detected_faces != 1:
                probe_failed_cnt += 1
                print('---> {} faces found in the image'.format(n_detected_faces))
                continue

            fp_probe_suc.write(line + '\n')
            if probe_cnt % 50 == 0:
                fp_probe_suc.flush()
                req_save_fps[api].flush()

            gt_in_gallery = name_id in gallery_unique_names
            if gt_in_gallery:
                pos_probe_cnt += 1
            else:
                neg_probe_cnt += 1

            max_idx = -1
            max_area = 0

            for face_idx, face in enumerate(detected_faces):
                pts = face["bounding_box"]["pts"]
                area = (pts[2][0] - pts[0][0]) * (pts[2][1] - pts[0][1])

                if max_area < area:
                    max_area=area
                    max_idx = face_idx

            print('---> max_idx={}, max_area={}'.format(max_idx, max_area))

            if max_idx > -1:
                matched_faces = detected_faces[max_idx].get("faces", None)

                if matched_faces is not None:
                    # print('resp-->\n',resp_dict["result"]["faces"][face_idx]
                    n_matched_faces = len(matched_faces)

                    print('face_idx=', max_idx,
                          ', n_matched_faces=', n_matched_faces)

                    if n_matched_faces == 0:
                        print('No match found, continue')
                        continue

                    topN_hit_list = []
                    for idx in range(top_n):
                        topN_hit_list.append(0)

                    for match_idx, match_face in enumerate(matched_faces):
                        # print("match_idx=",match_idx

                        if "id" in match_face:
                            matched_name_id = match_face["id"]
                            print("matched_id[{}]={}".format(
                                match_idx, matched_name_id))
                            print("matched_name[{}]={}".format(
                                match_idx, match_face["name"]))

                            # is_same = findSameId(url, name_id)

                            if(matched_name_id.strip() == name_id.strip() or
                                    match_face["name"].strip() == name_id.strip()):

                                print("Top {} HIT!!!!".format(match_idx+1))

                                for idx in range(match_idx, top_n):
                                    topN_hit_list[idx] = 1

                    if gt_in_gallery:
                        for idx, hit in enumerate(topN_hit_list):
                            pos_probe_topN_suc_cnt_list[idx] += hit
                    else:
                        for idx in range(top_n):
                            neg_probe_topN_fail_cnt_list[idx] += 1

    for (k, fp) in req_save_fps.items():
        # fp.write('\n]\n')
        fp.close()

    for (k, fp) in resp_save_fps.items():
        # fp.write('\n]\n')
        fp.close()

    fp_probe_list.close()
    fp_probe_suc.close()

    register_suc_rate = register_suc_cnt * 1.0 / gallery_list_cnt

    fn_out = osp.join(save_dir, '1vN_result.txt')
    fp_out = open(fn_out, 'w')

    write_str = '\n===================\n'

    write_str += 'register_suc_cnt = {}\n'.format(register_suc_cnt)
    write_str += 'gallery_list_cnt = {}\n'.format(gallery_list_cnt)
    write_str += 'register_suc_rate = %g%%\n\n' % (register_suc_rate*100)

    write_str += '\n===================\n'

    write_str += 'probe_cnt = {}\n'.format(probe_cnt)
    write_str += 'probe_failed_cnt = {}\n'.format(probe_failed_cnt)
    write_str += 'pos_probe_cnt = {}\n'.format(pos_probe_cnt)
    write_str += 'neg_probe_cnt = {}\n'.format(neg_probe_cnt)
    write_str += "pos_probe_topN_suc_cnt_list = {}\n".format(
        pos_probe_topN_suc_cnt_list)
    write_str += "neg_probe_topN_fail_cnt_list = {}\n".format(
        neg_probe_topN_fail_cnt_list)

    write_str += '\n===================\n'

    print(write_str)
    fp_out.write(write_str)

    for idx in range(top_n):
        if pos_probe_cnt == 0:
            recall = 1.0
        else:
            recall = pos_probe_topN_suc_cnt_list[idx] / float(pos_probe_cnt)

        if neg_probe_cnt == 0:
            fpr = 0.0
        else:
            fpr = neg_probe_topN_fail_cnt_list[idx] / float(neg_probe_cnt)

        tmp = pos_probe_topN_suc_cnt_list[idx] + \
            neg_probe_topN_fail_cnt_list[idx]
        if tmp == 0:
            precision = 1.0
        else:
            precision = pos_probe_topN_suc_cnt_list[idx] / float(tmp)

        miss_rate = 1 - recall

        # write_str = u"\n===> Top {}: \n".format(idx + 1)
        # write_str += u"    召回率=%g%%\n" % (recall * 100)
        # write_str += u"    漏报率=%g%%\n" % (miss_rate * 100)
        # write_str += u"    精度=%g%%\n" % (precision * 100)
        # write_str += u"    误报率=%g%%\n" % (fpr * 100)
        
        write_str = '\n===================\n'
        
        write_str += "---> Top {}: \n".format(idx + 1)
        write_str += "    recall rate = %g%%\n" % (recall * 100)
        write_str += "    miss rate = %g%%\n" % (miss_rate * 100)
        write_str += "    precision = %g%%\n" % (precision * 100)
        write_str += "    false positive reate = %g%%\n" % (fpr * 100)

        print(write_str)
        fp_out.write(write_str)

    fp_out.close()


if __name__ == '__main__':
    print(sys.argv)
    if len(sys.argv) < 2:
        # api_names='remove_gallery+create_gallery+add_face+search'
        api_names = 'remove_gallery+create_gallery+add_face+search'
        gallery_list_file = r"./gallery_10.txt"
        # gallery_list_file = r"register_suc_list.txt"
        probe_list_file = r"./probe_20.txt"
        # probe_list_file = 'probe_suc_list.txt'

        threshold = 0.4
        top_n = 6

        gallery_id = "1"

        save_dir = './1vN_results'
        config_file = 'facex_api_config_v2_argus.json'

        request_facex_api(api_names,
                          gallery_list_file,
                          probe_list_file,
                          threshold,
                          top_n,
                          gallery_id,
                          config_file,
                          save_dir)
    else:
        args = parse_args()
        request_facex_api(args.api_names,
                          args.gallery_list_file,
                          args.probe_list_file,
                          args.threshold,
                          args.top_n,
                          args.gallery_id,
                          args.config_file,
                          args.save_dir)
