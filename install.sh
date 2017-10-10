echo "##########################################################################"
echo "This script will install python-pip and pyserial. It will then create the"
echo "directory tacx-interface and download the required files."
echo "Run via sudo python ./tacx-interface.py"
echo "Options:"
echo "--debug to provide more output to screen"
echo "--simulate-trainer to ignore any trainer and provide ANT+ broadcast of "
echo "cadence=90rpm, power=283W, HT 72BPM"
echo "--power-factor to increase or decrease power broadcast."
echo "--power-factor=1.5 will result in a broadcast of 150W for 100W read at wheel"
echo "##########################################################################"
read -p "Press any key to start"
apt-get install python-pip
pip install pyserial
mkdir tacx-interface
cd tacx-interface
wget https://raw.githubusercontent.com/john-38787364/tacx-ant/master/tacx-interface.py
wget https://raw.githubusercontent.com/john-38787364/tacx-ant/master/ant.py
wget https://raw.githubusercontent.com/john-38787364/tacx-ant/master/T1932_calibration.py
echo "Installation finished"
echo "Now cd into tacx-interface and run sudo python ./tacx-interface.py"
read -p "Press any key to finish"