import sounddevice as sd

class PlaySound:
    def __init__(self, output_device_name="pulse") -> None:
        output_device_id = self._search_output_device_id(output_device_name)
        input_device_id = 0
        sd.default.device = [input_device_id, output_device_id]

    def _search_output_device_id(self, output_device_name, output_device_host_api=0) -> int:
        devices = sd.query_devices()
        output_device_id = None
        print("find sound device:" + output_device_name)

        for device in devices:
            print(device)
            is_output_device_name = output_device_name in device["name"]
            print(device["name"] + ":" + str(is_output_device_name))
            is_output_device_host_api = device["hostapi"] == output_device_host_api
            if is_output_device_name and is_output_device_host_api:
                output_device_id = device["index"]
                print("detect sound device:" + str(output_device_id))
                break

        if output_device_id is None:
            print("output_deviceが見つかりませんでした")
            exit()
            
        return output_device_id
    
    def play_sound(self, data, rate) -> bool:
        sd.play(data, rate)
        sd.wait()

        return True