cd /

cd usr/sbin/

/usr/sbin/alsactl --file /usr/share/doc/audioInjector/asound.state.RCA.thru.test restore

cd /

cd home/pi/Desktop/LED/FromSoundToLed/

git branch logBranch

git merge master

git add log

git commit -m "Automatic Test"

git push -u https://User:Password@github.com/Nablast/FromSoundToLed.git logBranch 

sudo python LedRaspberry.py &
