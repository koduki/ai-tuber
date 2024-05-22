# README


```bash
docker build -t koduki/obs .
```

```bash
docker run --rm -it -v .:/app -e YT_LIVE_KEY=${YOUR_YOUTUBE_LIVE_KEY} -p 6080:6080 koduki/obs
```