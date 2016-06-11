# emslave
Unit test slave configuration for Emscripten compiler buildbot slaves.

# Buildslave setup

1. Install python, pip and pip install buildbot-slave

2. Set up the buildslave directory (assumed at ~/emslave/):


    cd ~
    git clone https://github.com/juj/emslave

    cd ~/emslave/
    mkdir buildslave
    cd buildslave

    buildslave create-slave . demon.fi:9989 slavename slavepassword

3. Add ~/emslave/bin permanently to PATH, e.g.


    echo export PATH=\$PATH:~/emslave/bin > ~/.bash_profile

4. Set FIREFOX_STABLE_BROWSER environment variable, e.g.


    echo export FIREFOX_STABLE_BROWSER=/Applications/Firefox.app/Contents/MacOS/firefox > ~/.bash_profile

# Buildslave startup


    cd ~/emslave/buildslave
    buildslave start

# Ubuntu-specific setup

 - On a clean Ubuntu installation, some apt packages are needed:


    sudo apt-get install git buildbot-slave cmake openjdk-9-jre-headless

 - You may want to install Firefox via mozdownload to avoid the canonical plugins:

    sudo apt-get install python-pip
    pip install mozdownload
    ~/.local/bin/mozdownload --version=latest
    tar xjf firefox.tar.bz2
    # And add FIREFOX_STABLE_BROWSER="$HOME/firefox_stable/firefox" to .profile


 - Since running a buildslave, the following can be removed. The xul- plugins break the test runner if not removed.


    sudo apt-get -y remove unity-lens-shopping account-plugin-aim account-plugin-facebook account-plugin-flickr account-plugin-google account-plugin-icons account-plugin-identica account-plugin-jabber account-plugin-salut account-plugin-twitter account-plugin-windows-live account-plugin-yahoo gnome-online-accounts unity-control-center-signon xul-ext-webaccounts xul-ext-websites-integration xul-ext-ubufox
