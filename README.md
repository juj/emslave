# emslave
Unit test slave configuration for Emscripten compiler buildbot slaves.

# Prerequisites setup

0. On a build slave, 100GB of total hard disk space is preferable.

## Windows

1. Install Firefox Stable from https://www.mozilla.org/en-US/firefox/new/
2. Install Git for Windows for command line from https://git-scm.com/download/win
 - No need for Windows Explorer integration, can uncheck that
 - Set "Use Git from the Windows Command Prompt" (default)
 - Set "Use the OpenSSL library" (default)
 - Set "Checkout Windows-style, commit Unix-style line endings" (default)
 - Set "Use MinTTY" (default, does not really matter)
 - Disable "Enable file system caching" and "Enable Git Credential Manager" (neither of these are important for a CI server)
3. Install CMake from https://cmake.org/download/
 - During installation, check "Add CMake to the system PATH for all users"
4. Download Visual Studio 2017 Community
 - Do *not* log in to Visual Studio with user account, otherwise VS will periodically ask to re-login, breaking the CI infra builds from command line
 - Note: VS 2017 Express does not seem to work, as it apparently ships with only partial support for x64 building (32-bit building might work with Express, though untested)
5. Install Python 2.7.x from https://www.python.org/downloads/release/python-2714/
 - Make sure to choose the 64-bit (x86-64) installer, and not a 32-bit one.
 - Install for All Users, to directory C:\Python27\
 - Enable "Add python.exe to Path", make sure "pip" is checked
6. Install Python for Windows Extensions from https://sourceforge.net/projects/pywin32/files/pywin32/Build%20221/
 - Make sure to pick the 64-bit installer for Python 2.7, e.g. pywin32-221.win-amd64-py2.7.exe
7. Install 7-zip from http://www.7-zip.org/download.html
 - Add install directory (e.g. "C:\Program Files\7-Zip") to PATH for All Users
8. Install AWS Command Line Interface tools from https://aws.amazon.com/cli/ (64-bit Windows installer)
9. Set up $HOME/.aws with "config" and "credentials" files for pushing tagged builds to AWS

## Ubuntu Linux

 - On a clean Ubuntu installation, some apt packages are needed:

```bash
sudo apt update
sudo apt install git buildbot-slave cmake openjdk-9-jre-headless scons
```

 - You may want to install Firefox via mozdownload to avoid the canonical plugins:

```bash
sudo apt install python-pip
sudo -H pip install --upgrade pip
pip install mozdownload
cd ~
~/.local/bin/mozdownload --version=latest
tar xjf firefox.tar.bz2 # Could be under some other name, like firefox-58.0.2.tar.bz2
mv ~/firefox ~/firefox_stable
# And add export FIREFOX_STABLE_BROWSER="$HOME/firefox_stable/firefox" to .profile
```

 - Since running a buildslave, the following can be removed. The xul- plugins break the test runner if not removed.

```bash
sudo apt -y remove unity-lens-shopping account-plugin-aim account-plugin-facebook account-plugin-flickr account-plugin-google account-plugin-icons account-plugin-identica account-plugin-jabber account-plugin-salut account-plugin-twitter account-plugin-windows-live account-plugin-yahoo gnome-online-accounts unity-control-center-signon xul-ext-webaccounts xul-ext-websites-integration xul-ext-ubufox
```

# Buildslave setup

1. Install python, pip and pip install buildbot-slave:

```bash
sudo apt install python-pip
sudo -H pip install --upgrade pip
sudo -H pip install buildbot-slave
```

2. Set up the buildslave directory (assumed at ~/emslave/):

```bash
cd ~
git clone https://github.com/juj/emslave

cd ~/emslave/
mkdir buildslave
cd buildslave

buildslave create-slave . **address_to_build_master.com**:9989 **slavename** **slavepassword**
```

In above, replace address, port, slave name and password with the identifiers for the specific slave that is being set up.

3. Add ~/emslave/bin permanently to PATH, e.g.

    echo export PATH=\$PATH:~/emslave/bin >> ~/.bash_profile

4. Set SLAVE_ROOT environment variable, e.g.

    echo export SLAVE_ROOT=$HOME/emslave >> ~/.bash_profile

5. Set FIREFOX_STABLE_BROWSER environment variable, e.g.

    echo export FIREFOX_STABLE_BROWSER=/Applications/Firefox.app/Contents/MacOS/firefox >> ~/.bash_profile

# Buildslave startup

    cd ~/emslave/buildslave
    buildslave start

Note: on Ubuntu Linux, add the fields to ~/.profile, on macOS, to ~/.bash_profile

Note: on Windows, `buildslave start` must be run inside **Developer Command Prompt for VS2017**.