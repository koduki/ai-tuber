import obsws_python as obs

obs_password='j85l4lc0yoAlh7Ou'

client = obs.ReqClient(host='localhost', port=4455, password=obs_password, timeout=3)
resp = client.get_version()
print(f"OBS Version: {resp.obs_version}")

client.start_stream()
#client.stop_stream()
