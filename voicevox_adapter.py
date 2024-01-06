import json
import requests
import io
import soundfile

class VoicevoxAdapter:
    URL = 'http://localhost:50021/'

    def __init__(self) -> None:
        pass

    def __create_audio_query(self, text: str, speaker_id: int) -> json:
        item_data = {
            'text': text,
            'speaker': speaker_id,
        }
        response = requests.post(self.URL + 'audio_query', params=item_data)
        return response.json()
    
    def __create_request_audio(self, query_data, speaker_id:int) -> bytes:
        a_params = {
            'speaker' : speaker_id,
        }
        headers = {"accept": "audio/wav", "Content-Type":"application/json"}
        res = requests.post(self.URL + "synthesis", params=a_params, data=json.dumps(query_data), headers=headers)
        print(res.status_code)
        return res.content
    
    def get_voice(self, text:str):
        speaker_id = 58 # 猫使ビィ
        query_data:json = self.__create_audio_query(text, speaker_id=speaker_id)
        audio_bytes = self.__create_request_audio(query_data, speaker_id=speaker_id)
        audio_stream = io.BytesIO(audio_bytes)
        data, sample_rate = soundfile.read(audio_stream)

        return data, sample_rate
    
if __name__ == "__main__":
    from play_sound import PlaySound

    input_str = "いらっしゃいませ"
    voicevox_adapter = VoicevoxAdapter()
    play_sound = PlaySound("スピーカー (Realtek(R) Audio)")
    # play_sound = PlaySound("CABLE Input")
    data, rate = voicevox_adapter.get_voice(input_str)
    print(rate)

    play_sound.play_sound(data, rate)