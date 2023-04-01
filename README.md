# vkb_led_jg_plugin

A Joystick Gremlin plugin to activate the LEDs of a VKB flight stick

***Warning***: this code interfaces with your VKB device. I have found this
code safe to use, but you assume all risks when applying your device.  

## Directions
 
 1. Save the bitstruct & pywinsub folders to the Joystick Gremlin
    programs directory.  For me this is:
        C:\Program Files (x86)\H2ik\Joystick Gremlin
 2. Save vkb_led_jg_plugin_lib.py to the same Joystick Gremlin directory
 3. Save vkb_led_jg_plugin.py in a conveniently accessible directory.
 4. In vkb_led_jg_plugin.py, the product id is set for a right-handed 
    Gladiator NXT.  This plugin SHOULD work with a left-handed Gladiator and
	both left and right handed Omni throttles as well as older Gladiators
	that have a base LED (blue and red), a hat LED (red) and a RGB LED.
	Edit the file with a text editor and enter in the product id.
 5. Open Joystick Gremlin, go to the Plugins tab, and choose Add Plugin,
    and navigate to where vkb_led_jg_plugin.py is located.
 6. Select desired settings...

## Credit Where Credit Is Due
 
* pywinsub written by Rene F. Aguirre located at pypi.org/project/pywinusb

*  bitstruct written by Erik Moqvist & Ilya Petukhov located at
    pypi.org/project/bitstruct
 
* pyvkb written by ventorvar located at github.com/ventorvar/pyvkb.  The code
    for the LEDClass, get_LED_congifs(), set_LEDs() and LED_conf_checksum() are
	slightly modified but essentially from this package.  Modifications include
	simplifying the RGB colors to use the VKB 0-7 range, opening and closing 
	the device, and working around an issue with reading in values from the VKB
	device (described below).
	
* vkb-msfs-led by tiberriusteng located at github.com/tiberiusteng/vkb-msfs-led.
    Mostly used as an example and for inspiration.
	
And, of course, Joystick Gremlin by whitemagic located at 
    whitemagic.github.io/JoystickGremlin/

## Details

In the plugin user interface, you can associate a button with one LED.  After 
choosing either the Base, Hat, or RGB LED, you can set the configuration for 
that LED.  Each of the 3 LEDs use the color mode, led mode, and rgb colors 
differently and thus each LED has a separate section on the UI.  Only the 
settings of the selected LED will be applied.

The USB Lighting Usage report stored in the flight stick will hold the current
state of the active LEDs.  A change to that LED will wipe out the prior state.
Thus, the recorded history of LED use is only the current configurations.

In the plugin code, the decorated function deals with the button state and the
"while pressed" option.  A button starts in the "off" state.  With the button 
push, the current settings for the linked LED is saved from the stick, and the
new LED settings are set.  The button state is now "on".

When the button is released, and if the "while pressed" option is on, the prior
LED settings are restored.  The button state is turned "off".

If the "while pressed" option is off, the button state is "on", and the button
is pressed, the code looks in the usage report to see if the stick's LED 
configuration matches the button's LED configuration.  If they match, then the
LED is reset to the default color.  If they do not match, then another 
button has been pressed which changed the LED and the LED is left alone.
The button state is turned "off".

## Limitations

The LED settings stored in the VKB device via VKBDevCFG are overwritten during
the plugin's use, but those settings will be restored when the device is 
unplugged and re-plugged in.

The same LED can be activated by different buttons.  For example, button 1
could turn the RGB to purple, and button 2 could turn it to green.  If button 1
is pressed (purple) and button 2 is pressed with the "while pressed" option 
(green), the color will reset to purple when the button 2 is released.  
However, if button 2 is not "while pressed" (green) and pressed again, the LED 
will be set to the default, NOT purple.  Button 1 still "on" however, and its 
"on" state will be synced to the LED.  Another press of button 1 will not light
the LED (because it will then be in the "off" state).  Yet another press of 
button 1 will turn the LED back on.  This happens because any number of buttons
could potentially activate the LED.  My priority was to sync the "on" state to
LED activation as opposed to toggling the LED with every button press.

When there are 2 or 3 LEDs set (of the 3 possible) and those settings are 
pulled from the device, there is always an error in the last LED configuration:
the LED mode is 0.  To circumnavigate this situation a "dummy" LED is always 
added to the LED list.  The dummy code is ignored when reading the settings 
back in.

The plugin does not interact with the flight simulator/game in anyway.  If LEDs
are set when the sim ends, you will have to push buttons to get back to a
neutral state, or simply, unplug and re-plug the device back in.

## Future Features

 1. Track the history of button pushes across all buttons to have a more 
    educated restore procedure.
 2. Replace the hard-coded product id with a button push input via the 
    interface.
 3. Utilize dropdown controls in UI when they are implemented in JG (the code
    is in JG but they are not currently functioning).
