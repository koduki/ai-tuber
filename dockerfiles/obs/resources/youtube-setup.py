import json
import os

wk_dir = '/root/.config/obs-studio/basic/profiles/Untitled/'
template_file = "service.json.template"
output_file = "service.json"
stream_key = os.environ.get("YT_LIVE_KEY")

with open(wk_dir + template_file, "r") as f:
    template = json.load(f)

template["settings"]["key"] = stream_key

with open(wk_dir + output_file, "w") as f:
    json.dump(template, f, indent=4)
