cd ~/emslave
git pull

cd ~/emslave/emsdk
git pull
./emsdk install sdk-incoming-64bit
./emsdk activate --embedded sdk-incoming-64bit
