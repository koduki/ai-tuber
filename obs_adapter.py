import os
import obsws_python as obs

class ObsAdapter:
    host = "localhost"
    port = 4455
    password = os.environ["OBS_WS_PASSWORD"]

    def __init__(self) -> None:
        self.client = obs.ReqClient(host=self.host, port=self.port, password=self.password, timeout=3)
    
    def visible_avater(self, name):
        for item in self.client.get_scene_item_list("s001").scene_items:
            item_id = item["sceneItemId"]
            if item["sourceName"] == name:
                self.client.set_scene_item_enabled("s001", item_id, True)
            else:
                self.client.set_scene_item_enabled("s001", item_id, False)

if __name__ == "__main__":
    import time

    obs = ObsAdapter()
    obs.visible_avater("normal")
    time.sleep(1)

    obs.visible_avater("joyful")
    time.sleep(1)

    obs.visible_avater("fun")
    time.sleep(1)

    obs.visible_avater("sad")
    time.sleep(1)

    obs.visible_avater("angry")
    time.sleep(1)

    obs.visible_avater("normal")
    time.sleep(1)