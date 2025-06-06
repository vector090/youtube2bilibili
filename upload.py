import json
import os
import re
import shutil
import sys
import time
import base64
import shlex
import requests
import yt_dlp
from PIL import Image
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

OWNER_NAME = "username"
REMOVE_FILE = True  # 是否删除投稿后的视频文件
LineN = "qn"  # 线路 cos bda2 qn ws kodo
DEFAULT_TID = 21
PROXY = 'http://127.0.0.1:10809'
COOKIES_FROM_BROWSER = ("firefox",)
URL_LIST_FILE = "url_list.json"
POTOKEN_PATH = "D:\\potoken.txt"

def read_potoken():
    """从文件读取potoken"""
    try:
        with open(POTOKEN_PATH, "r") as f:
            potoken = f.read().strip()
        return potoken
    except Exception as e:
        print(f"Error reading potoken: {e}")
        return ""

def escape_description(description):
    return shlex.quote(description)

def get_double(s):
    return '"' + s + '"'

def cover_webp_to_jpg(webp_path, jpg_path):
    im = Image.open(webp_path).convert("RGB")
    im.save(jpg_path, "jpeg")
    im.close()

def download(youtube_url, folder_name):
    # 每次下载前读取最新的potoken
    potoken = read_potoken()
    full_potoken = "web.gvs+" + potoken
    
    ydl_opts = {
        "outtmpl": "./videos/" + str(folder_name) + "/%(id)s.mp4",
        "cookiesfrombrowser": COOKIES_FROM_BROWSER,
        "live_from_start": True,
        "concurrent_fragment_downloads": 3,
        "fragment_retries": 3,
        "proxy": PROXY,
        "extractor_args": {
            "youtube": {
                # Correct way to pass player_client
                "player_client": ["default", "-tv", "web_safari", "web_embedded"],
                # 使用从文件读取的potoken
                "po_token": [full_potoken]
            }
        }
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([youtube_url])

def get_info(url):
    # 每次获取信息前读取最新的potoken
    potoken = read_potoken()
    full_potoken = "web.gvs+" + potoken
    
    ydl_opts = {
        "cookiesfrombrowser": COOKIES_FROM_BROWSER,
        'proxy': PROXY,
        "extractor_args": {
            "youtube": {
                "player_client": ["default", "-tv", "web_safari", "web_embedded"],
                "po_token": [full_potoken]
            }
        }
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return info

def getVideoPath(id_):
    path = "./videos/" + str(id_)
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.find(id_) != -1:
                return os.path.join(root, file)

def download_image(url, id_):
    proxies = {
        "http": PROXY,
        "https": PROXY,
    }
    r = requests.get(url, stream=True, proxies=proxies)
    f = open("./videos/" + str(id_) + "/cover.webp", "wb")
    for chunk in r.iter_content(chunk_size=102400):
        if chunk:
            f.write(chunk)
    f.close()

def judge_chs(title):
    for i in title:
        if "\u4e00" <= i <= "\u9fa5":
            return True
    return False

def get_base64(string):
    return str(base64.b64encode(string.encode("utf-8")).decode("utf-8"))

def get_base64_twice(string):
    i = 0
    while i < 2:
        string = get_base64(string)
        i += 1
    return string

def get_chs_title(title):
    while True:
        publish_title = get_base64(title)
        if len(publish_title) > 80:
            title = title[:-1]
            continue
        else:
            return publish_title

def get_chs_title_twice(title):
    i = 0
    while i < 2:
        title = get_chs_title(title)
        i += 1
    return title

def cut_tags(tags):
    i = 0
    while len(tags) > i:
        if len(tags[i]) > 20:
            tags[i] = tags[i][:20]
        i += 1
    return tags

def get_release_date(youtube_url):
    # 每次获取信息前读取最新的potoken
    potoken = read_potoken()
    full_potoken = "web.gvs+" + potoken
    
    ydl_opts = {
        'proxy': PROXY,
        'cookiesfrombrowser': COOKIES_FROM_BROWSER,
        'quiet': True,
        "extractor_args": {
            "youtube": {
                "player_client": ["default", "-tv", "web_safari", "web_embedded"],
                "po_token": [full_potoken]
            }
        }
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        result = ydl.extract_info(youtube_url, download=False, **{'force_generic_extractor': True})
        release_date = result.get('upload_date')
        if release_date:
            return release_date[:4] + '年' + release_date[4:6] + '月' + release_date[6:] + '日'
        return '未知日期'

def biliup_upload(vUrl, TID, title, dynamic_title, description, tags, videoPath, cover):
    release_date = get_release_date(vUrl)
    desc = f"原视频日期{release_date}"
    strTags = ",".join(tags)
    CMD = (
         ".\\biliup upload "
        + videoPath
        + " --desc "
        + get_double(desc)
        + " --copyright 2 "
        + "--tag "
        + get_double(strTags)
        + " --tid "
        + str(TID)
        + " --source "
        + get_double(vUrl)
        + " --line "
        + LineN
        + " --title "
        + get_double(title)
        + " --cover "
        + str(cover)
    )
    print("[🚀 origin title]: ", title)
    print("[🚀 Start to using biliup, with these CMD commend]:\n", CMD)
    biliupOutput = "".join(os.popen(CMD).readlines())
    return "投稿成功" in biliupOutput or "标题相同" in biliupOutput

def process_video(vUrl, TID):
    try:
        info = get_info(vUrl)
        title = info["title"]
        dynamic_title = title
        author = info["uploader"]
        id_ = info["id"]
        description = info["description"]
        tags = info["tags"]
        cover = info["thumbnail"]
        tags.append(author)
        tags.append(OWNER_NAME)

        try:
            os.mkdir(path="./videos/" + str(id_))
        except FileExistsError:
            shutil.rmtree("./videos/" + str(id_))
            os.mkdir(path="./videos/" + str(id_))

        download(vUrl, id_)
        download_image(cover, id_)
        cover_webp_to_jpg("./videos/" + str(id_) + "/cover.webp", "./videos/" + str(id_) + "/cover.jpg")

        if len(title) > 80:
            title = title[:80]

        if len(description) > 250:
            description = description[:250]
        if len(tags) > 10:
            tags = tags[:10]
        tags = cut_tags(tags)

        videoPath = getVideoPath(id_)
        cover_path = "./videos/" + str(id_) + "/cover.jpg"

        success = biliup_upload(vUrl, TID, title, dynamic_title, description, tags, videoPath, cover_path)
        
        if success and REMOVE_FILE:
            shutil.rmtree("./videos/" + str(id_))
        
        return success
    except Exception as e:
        print(f"Error processing video {vUrl}: {e}")
        return False

def load_url_list():
    if os.path.exists(URL_LIST_FILE):
        with open(URL_LIST_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_url_list(url_list):
    with open(URL_LIST_FILE, "w", encoding="utf-8") as f:
        json.dump(url_list, f, ensure_ascii=False, indent=4)

def mode_single_video():
    url = input("请输入视频URL: ")
    tid = input("请输入分区代码 (默认21): ")
    if not tid:
        tid = DEFAULT_TID
    else:
        tid = int(tid)
    process_video(url, tid)

def mode_video_list():
    potoken = read_potoken()
    full_potoken = "web.gvs+" + potoken
    
    url = input("请输入视频列表或频道URL: ")
    os.system(f'yt-dlp --flat-playlist --dump-single-json --cookies-from-browser firefox --proxy {PROXY} --extractor-args youtube:po_token={full_potoken} {url} > output.json')

    with open('output.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    url_list = [{"url": entry["url"], "status": "no", "count": 0} for entry in data["entries"] if entry["url"].startswith("https://www.youtube.com")]

    save_url_list(url_list)
    print("以下是需要上传的视频URL列表:")
    for entry in url_list:
        print(entry["url"])

    confirm = input("请确认以上URL是否正确 (yes/no): ")
    if confirm.lower() != "yes":
        print("操作已取消。")
        return
    
    tid = input("请输入分区代码 (默认21): ")
    if not tid:
        tid = DEFAULT_TID
    else:
        tid = int(tid)
    
    for entry in url_list:
        if entry["status"] == "no":
            for _ in range(2):  # 尝试2次
                success = process_video(entry["url"], tid)
                if success:
                    entry["status"] = "yes"
                    break
                entry["count"] += 1
            save_url_list(url_list)

def mode_resume_upload():
    tid = input("请输入分区代码 (默认21): ")
    if not tid:
        tid = DEFAULT_TID
    else:
        tid = int(tid)
    
    url_list = load_url_list()
    for entry in url_list:
        if entry["status"] == "no":
            for _ in range(2):  # 尝试2次
                success = process_video(entry["url"], tid)
                if success:
                    entry["status"] = "yes"
                    break
                entry["count"] += 1
            save_url_list(url_list)

def mode_manual_playlist():
    urls = []
    while True:
        url = input("请输入视频URL (输入'完毕'结束): ")
        if url.lower() == '完毕':
            break
        urls.append({"url": url, "status": "no", "count": 0})

    if not urls:
        print("没有输入任何URL。")
        return

    save_url_list(urls)
    
    print("以下是需要上传的视频URL列表:")
    for entry in urls:
        print(entry["url"])

    confirm = input("请确认以上URL是否正确 (yes/no): ")
    if confirm.lower() != "yes":
        print("操作已取消。")
        return
    
    tid = input("请输入分区代码 (默认21): ")
    if not tid:
        tid = DEFAULT_TID
    else:
        tid = int(tid)
    
    for entry in urls:
        if entry["status"] == "no":
            for _ in range(2):  # 尝试2次
                success = process_video(entry["url"], tid)
                if success:
                    entry["status"] = "yes"
                    break
                entry["count"] += 1
            save_url_list(urls)

def main():
    print("请选择模式:")
    print("1: 单视频上传模式")
    print("2: 视频列表或频道模式")
    print("3: 断点续传模式")
    print("4: 手动输入多个单视频链接模式")
    mode = input("请输入模式编号: ")
    
    if mode == "1":
        mode_single_video()
    elif mode == "2":
        mode_video_list()
    elif mode == "3":
        mode_resume_upload()
    elif mode == "4":
        mode_manual_playlist()
    else:
        print("无效的模式编号。")

if __name__ == "__main__":
    main()
