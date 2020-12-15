# radio_rasp_python

* The rasp_pi_andr_bluetooth_radio.py script is being used to connect the XBee radio module to the Android device.
  * Place the Bluetooth interface mac address, of the device on which the script is being ran on, on the following [line](https://github.com/ManinderjitS/radio_rasp_python/blob/43b6483219d50525d1beb7222c6617b3468de242/rasp_pi_andr_bluetooth_radio.py#L29) .
  * The radio module needs to be physically connected to the device where the script is running.
    * Use a micro usb to make this physical connection.
    * The radio module needs to be connected to the device before the script is ran.
  * For the bluetooth part of this script to work, the device running the script needs to have at the very least bluetooth capabilities built in it.
    * USB bluetooth extensions haven't been tested yet.
* This is a Python3 script.

# To run the script
* First download the appropriate libraries in the script.
* Then run it with the following command:
 `python3 rasp_pi_andr_bluetooth_radio.py`

## The second file in the folder, `phone_to_pi.py`, is not meant to be used.
