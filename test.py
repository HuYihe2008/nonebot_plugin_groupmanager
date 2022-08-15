import json
import requests
import gc
version_url = requests.get("https://api.jamyido.tk/admin-version.json")
new_version = version_url.text
version_data = json.loads(new_version)
version = version_data[0]
__help__version__ = ('0.6.2.5 ' + "(最新版本：" + (version['version']) + " by " + (version['author']) + ")")
print(__help__version__)
gc.collect()