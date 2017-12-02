cd /

cd home/pi/Desktop/LED/FromSoundToLed/

# git pull 

!/bin/bash
until sudo python LedRaspberry.py; do
    echo "'LedRaspberry.py' crashed with exit code $?. Restarting..." >&2
    sleep 1
done

