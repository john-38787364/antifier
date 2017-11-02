apt-get install python-pip python-tk
pip install pyserial pyusb numpy scipy
mkdir antifier
cd antifier
wget --quiet https://raw.githubusercontent.com/john-38787364/antifier/master/antifier.py
wget --quiet https://raw.githubusercontent.com/john-38787364/antifier/master/ant.py
wget --quiet https://raw.githubusercontent.com/john-38787364/antifier/master/trainer.py
wget --quiet https://raw.githubusercontent.com/john-38787364/antifier/master/FortiusSWPID1942Renum.hex
wget --quiet https://raw.githubusercontent.com/john-38787364/antifier/master/fxload-libusb.exe
wget --quiet https://raw.githubusercontent.com/john-38787364/antifier/master/power_calc_factors_custom.txt
wget --quiet https://raw.githubusercontent.com/john-38787364/antifier/master/power_calc_factors_fortius.txt
wget --quiet https://raw.githubusercontent.com/john-38787364/antifier/master/power_calc_factors_imagic.txt
wget --quiet https://raw.githubusercontent.com/john-38787364/antifier/master/README.txt
wget --quiet https://raw.githubusercontent.com/john-38787364/antifier/master/tacx_trainer_debug.py
echo "##########################################################################"
echo "This script has installed python-pip and pyserial. It has created the"
echo "directory antifier and downloaded the required files."
echo "##########################################################################"
echo "Installation finished"
echo "Now cd into antifier and read README.txt, then run sudo python ./antifier.py"
