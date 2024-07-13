import requests
import datetime

def get_memorial():
    today = datetime.date.today()
    mmdd = today.strftime('%m%d')

    url = "https://api.whatistoday.cyou/v2/anniv/" + mmdd

    r = requests.get(url).json()

    return r['_items'][0]['anniv1']