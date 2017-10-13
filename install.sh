apt-get install python-pip
pip install pyserial pyusb
mkdir tacx-interface
cd tacx-interface
wget --quiet https://raw.githubusercontent.com/john-38787364/tacx-ant/master/tacx-interface.py
wget --quiet https://raw.githubusercontent.com/john-38787364/tacx-ant/master/ant.py
wget --quiet https://raw.githubusercontent.com/john-38787364/tacx-ant/master/T1932_calibration.py
wget --quiet https://raw.githubusercontent.com/john-38787364/tacx-ant/master/runoff_calibration.py
echo "##########################################################################"
echo "This script has installed python-pip and pyserial. It has created the"
echo "directory tacx-interface and downloaded the required files."
echo "Run via sudo python ./tacx-interface.py"
echo "Options:"
echo "--debug to provide more output to screen"
echo "--simulate-trainer to ignore any trainer and provide ANT+ broadcast of "
echo "cadence=90rpm, power=283W, HT 72BPM"
echo "--power-factor to increase or decrease power broadcast."
echo "--power-factor=1.5 will result in a broadcast of 150W for 100W read at wheel"
echo "##########################################################################"
echo "Installation finished"
echo "Now cd into tacx-interface and run sudo python ./tacx-interface.py"
echo "To calibrate trainer run sudo python ./runoff_calibration.py"
