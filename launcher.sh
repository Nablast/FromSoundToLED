cd /

cd usr/sbin/

/usr/sbin/alsactl --file /usr/share/doc/audioInjector/asound.state.RCA.thru.test restore

cd /

cd home/pi/Desktop/LED/FromSoundToLed/

git checkout logBranch

git merge origin/master

git add log

git commit -m "Automatic Push"

git push -u https://Nablast:GBtWSKgJ3@github.com/Nablast/FromSoundToLed.git logBranch 

sudo python LedRaspberry.py &
