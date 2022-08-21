import json
import requests
from nonebot_plugin_admin_hello.path import *
version_url = requests.get("https://api.jamyido.tk/admin-version.json")
new_version = version_url.text
version_data = json.loads(new_version)
version = version_data[0]
__help__version__ = (
        "当前版本：" + version_id + "\n" +
        "最新正式版本：" + (version['version']) + "\n" +
        "beta版本：" + (version['version_beta']) + "\n" +
        "Copyright © by " + (version['author']) + " All Rights Reserved." + "\n" +
        "https://jamyido.tk/"
)
print(__help__version__)
