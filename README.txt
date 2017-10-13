OVERVIEW
This project will enable a Windows or Linux PC to broadcast ANT+ data via a dongle from a Tacx trainer connected to it via USB. This can be either be from a standalone PC broadcasting to a PC or tablet running e.g. Zwift or Trainerroad, or from a Windows PC already running Zwift/ Trainerroad (this PC will therefore require two ANT+ dongles) 
Home page: https://github.com/john-38787364/tacx-ant

REQUIREMENTS
- Windows or Linux PC
- ANT+ dongle to broadcast data - standard Garmin and Suunto dongles tested. Any dongle with hardware ID 0fcf:1009 or 0fcf:1008 should work
- Tacx trainer. So far tested with 1932 head unit:
https://github.com/john-38787364/tacx-ant/blob/master/1932.jpg

INSTALLATION
Linux (Root required):
sudo curl https://raw.githubusercontent.com/john-38787364/tacx-ant/master/install.sh | sudo bash  
This will create a directory tacx-interface with required scripts in. 

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
https://github.com/john-38787364/tacx-ant/raw/master/dist/tacx-interface.exe
Optionally dowload the calibration app:
https://github.com/john-38787364/tacx-ant/raw/master/dist/runoff_calibration.exe

Run by double clicking on the downloaded EXE

USAGE
Linux
sudo python tacx-interface.py

Windows
1. Quit Garmin express if running
2. Run application- a black screen should open. If it opens then closes then you've got a problem (see debug options below)
(3. Start Zwift - Power, Heart rate, Cadence and Smart Trainer should all be available as FE-C device )

OPTIONS
--power-factor=x - will alter power reported by factor selected. Defaults to 1. e.g. power-factor=0.9 and power is 100, then power of 90W will be reported

PROBLEMS
1. Unplug and replug USB ANT+ dongles if having problems! Some applications esp Garmin Express can be greedy about ownership of dongles
2. Open a command prompt and from the download directory and run the program with the following switches:
--debug - starts verbose output from script
--simulate-trainer - will ignore if a trainer is connected and sends cadence=90, power=283, HR=72
e.g. save output with tacx-interface.py/.exe --debug > out.log

3. Report all issues via github at https://github.com/john-38787364/tacx-ant

CALIBRATION
As the trainer does not report power, power must be inferred by the following formula:

speed x resistance exerted by the trainer.

The file T1932_calibration.py contains the resistance values on the trainer in response to the slope indicated by the training program, as well as the fomulae to calculate power at each resistance level.

Change the resistance exerted by the trainer for grade sent by training application:
Alter the list variable "grade_resistance" values to match the resistance level you want at grades up to the value you input.
e.g.
grade_resistance = [
-3,     #up to grade -3% will cause trainer to exert resistance level 1
-2,     #from grade >-3% to <=-2% will cause trainer to exert resistance level 2
-1,     #from grade >-2% to <=-1% will cause trainer to exert resistance level 3 etc.
... etc.

The resistance level 7 was most extensively tested for power calculations so it is recommended that grades 0-2% are around this level

To change the power calculation:
The basic formula is speed x resistance level. Each resistance level is contained within the "factors" dictionary variable as
resistance level:[multiplier],[additional power]
so the power output at a particular resistance = speed * multiplier + additional power
e.g.
factors={
1:[4.5,-20],#i.e. for resistance level 1, power = speed(kph) x 4.5 + (-20) watts = 20kph  x 4.5 - 20 = 70 watts

The "factors" dictionary variable has been derived from tests using values from a Powertap hub vs speed/resistance level.
The runoff_calibration.py script will help you get your trainer closer to these test conditions and hence a more accurate power value.
You may alter the multiplier and additional power values for each resistance level to more closely match your personal setup


