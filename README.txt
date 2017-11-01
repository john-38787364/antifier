OVERVIEW
This project will enable a Windows or Linux PC to broadcast ANT+ data via a dongle from a Tacx trainer connected to it via USB. This can be either be from a standalone PC broadcasting to a PC or tablet running e.g. Zwift or Trainerroad, or from a Windows PC already running Zwift/ Trainerroad (this PC will therefore require two ANT+ dongles) 
Home page: https://github.com/john-38787364/antifier

REQUIREMENTS
- Windows or Linux PC
- ANT+ dongle to broadcast data - standard Garmin and Suunto dongles tested. Any dongle with hardware ID 0fcf:1009 or 0fcf:1008 should work
- Tacx trainer. So far tested with 1932 and 1942 head unit

INSTALLATION
Linux (Root required):
sudo curl https://raw.githubusercontent.com/john-38787364/antifier/master/install.sh | sudo bash  
This will create a directory "antifier" with required scripts in. 

Windows:
You will need to reinstall your trainer as a libusb-win32 device:
1. Open device manager, right click on the device and click "Uninstall". It may be listed as a "Jungo" device 
(see http://www.tacxdata.com/files/support/Windows10driverissues.pdf - DO NOT RUN TacxDriversSetup.exe!)
2. Unplug the trainer, wait 5 seconds, and plug it back in again
3. Find it again (usually under other devices>VR-interface)
4. Right click and select "update driver software"
5. Select "Browse my computer for driver software"
6. Select "Let me select from a list of device drivers on my computer"
7. Select libusb-win32 devices
8. Select ANT USB Stick 2, then OK in the warning, then close

Download the Windows build of the application from:
https://github.com/john-38787364/antifier/raw/master/dist/tacx-interface.exe

Double click on the self extracting package and run by double clicking on the downloaded antifier.exe

If you wish to run as a native python script then you will need to run python.exe -m pip install pyusb and to download libusb-win32-devel-filter:
https://sourceforge.net/projects/libusb-win32/files/libusb-win32-releases/1.2.6.0/

USAGE
Linux
sudo python antifier.py

Windows
1. Quit Garmin express if running
2. Run application- the gui should open

Both
1. Pick the appropriate power curve for your trainer under "setup"
2. Scan for hardware to pickup your trainer and ANT dongle
3. Perform a rundown test to calibrate your trainer. (see below)
4. Start Zwift/ Trainerroad - Power, Heart rate, Cadence and Smart Trainer should all be available as FE-C device 

Rundown test
To ensure comparable training sessions, the trainer should exert the same relative resistance each time
1. Aim for about 100psi in tyre when cold
2. Warm up for 2-3 minutes to warm rubberer
3. Perform test- try for about a 7 second rundown from 40kph

OPTIONS
-p, --power-factor=x - will alter power reported by factor selected. Defaults to 1. e.g. power-factor=0.9 and power is 100, then power of 90W will be reported

PROBLEMS
1. Unplug and replug USB ANT+ dongles if having problems! Some applications esp Garmin Express can be greedy about ownership of dongles
2. Open a command prompt and from the download directory and run the program in the console with the following switches:
-d, --debug - starts verbose output from script
-s, --simulate-trainer - will ignore if a trainer is connected and sends cadence=90, power, HR=72 to test if your ANT+ dongle is broadcasting correctly, and if Zwift is receiving
save output with antifier.py/.exe --debug > out.log

To run the program in the console in Windows:
2.1 Open the folder containing tacx-interface.exe then press "Shift Key" and right click in the white space next to it, then select "Open command window here". A black window should open
2.2 Run the script with "antifier.exe --debug > out.log"
(select this command without the quotes then copy, right click on the black window should paste it into the black window)
2.3 Press return- there should be no output on the screen
2.4 Take a short Zwift ride- you should get data from your trainer on Zwift
2.5 Finish the ride then press ctrl-c whilst in the black window to exit the script
2.6 Post out.log to github as an issue

3. Report all issues via github at https://github.com/john-38787364/antifier

POWER AND RESISTANCE CALIBRATION
As the trainer does not report power, power must be inferred by the following formula:

speed x resistance exerted by the trainer.

The powercurve files power_calc_factors_TRAINER.txt contain the factors rewuired by the calculation as well as grade informtaion. You select which file to use when you choose a powercurve under "setup".

Format: (comments after # sign)
#grade:multiplier,additional
-3:4.5000,-20 #1st line- any grade up to -3% will exert resistance level 0; power = speed x 4.5 + (-20) watts = 20kph x 4.5 - 20 = 70 watts
-2:5.3666,-29 #2nd line- grades from -3% to -2% will exert resistance level 1; power = speed x 5.3666 + (-29) = 20kph x 5.3666 -29 =  78 watts

Resistance level 6 was most extensively tested for power calculations so it is recommended that grades 0-2% are around this level

Alter the grade and factors as you see fit. However, ensure there are 14 grades/ resistance value defined


