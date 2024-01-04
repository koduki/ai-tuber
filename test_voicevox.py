from voicevox_adapter import VoicevoxAdapter
from play_sound import PlaySound

input_str = "いらっしゃいませ"
voicevox_adapter = VoicevoxAdapter()
play_sound = PlaySound("スピーカー (Realtek(R) Audio)")
data, rate = voicevox_adapter.get_voice(input_str)
play_sound.play_sound(data, rate)