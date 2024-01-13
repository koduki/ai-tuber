import os
import obsws_python as obs

class ObsAdapter:
    def __init__(self) -> None:
        host = "localhost"
        port = 4455
        password = os.environ["OBS_WS_PASSWORD"]

        self.client = obs.ReqClient(host=host, port=port, password=password, timeout=3)
    
    def visible_avater(self, name):
        for item in self.client.get_scene_item_list("s001").scene_items:
            item_id = item["sceneItemId"]
            if item["sourceName"] == name:
                self.client.set_scene_item_enabled("s001", item_id, True)
            elif(not item["sourceName"].startswith("LLM") and not item["sourceName"].startswith("BGM")):
                self.client.set_scene_item_enabled("s001", item_id, False)

    def visible_llm(self, name):
        for item in self.client.get_scene_item_list("s001").scene_items:
            item_id = item["sceneItemId"]
            if item["sourceName"] == "LLM_" + name:
                self.client.set_scene_item_enabled("s001", item_id, True)
            elif(item["sourceName"].startswith("LLM") and not item["sourceName"].startswith("BGM")):
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

    obs.visible_llm("gemini")
    time.sleep(1)

    obs.visible_llm("gpt4")
    time.sleep(1)