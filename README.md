# tkgpio
A Python library to simulate electronic devices connected to the GPIO on a Raspberry Pi, using TkInter.

<img src="https://user-images.githubusercontent.com/2084188/92945917-5a5cf000-f42c-11ea-820d-e460cf53e5b0.png" width="600">

## Fork pre 2020-07
* Hasta commit 6dce7022e26f8af17baf68e310c8e334d38361c5
* Sin incluir añadido de motores, servos,...
* Desactiva el efecto de sonido que da errores para instalar.

* Instalar desde GitHub
`pip install --force-reinstall --no-deps git+https://github.com/rubennj/tkgpio.git`

## About

Due to the Coronavirus outbreak in 2020, students enrolled in my Microcontroller course could not use the laboratory. So I decided to build a Raspberry Pi circuit simulator, to make remote class activities possible. And it works pretty well!

The main goal here is to enable students to use the same APIs that control physical devices connected to the GPIO, but interacting with a GUI instead. I'm not worried about creating a realistic electronic simulation.

Since we were already using Python to program on Raspberry Pi, I've built the interface with TkInter. Some libraries (like gpiozero) allowed me to easily mock the devices in the GUI. In other cases, I had to reimplement the API inside the library – but since I can temporaraly add folders to Python's PATH, `import` commands keep working exactly as the original ones.

TkGPIO currently supports the following devices:

- Some [gpiozero](https://github.com/gpiozero/gpiozero) components (more coming soon)
  - LED / PWMLED
  - (Active) Buzzer
  - Button
  - Distance Sensor (HC-SR04)
  - Light Sensor (LDR)
  - Motion Sensor (HC-SR501)
- LCD display (reimplementing [Adafruit_CharLCD API](https://github.com/adafruit/Adafruit_Python_CharLCD))
  - Only `message` and `clear` methods are supported for now (more coming soon)
- Infrared emmitter (reimplementing [py_irsend API](https://github.com/ChristopherRogers1991/python-irsend))
- Infrared receiver (reimplementing [python-lirc API](https://github.com/tompreston/python-lirc))


## Usage

This is a simple example to create and control 2 LEDs and 1 Button.

<img src="https://user-images.githubusercontent.com/2084188/92954753-5c2db000-f43a-11ea-8a73-22e9e337c785.png" width="300">

```python3
from tkgpio import TkCircuit

# initialize the circuit inside the 

configuration = {
    "width": 300,
    "height": 200,
    "leds": [
        {"x": 50, "y": 40, "name": "LED 1", "pin": 21},
        {"x": 100, "y": 40, "name": "LED 2", "pin": 22}
    ],
    "buttons": [
        {"x": 50, "y": 130, "name": "Press to toggle LED 2", "pin": 11},
    ]
}

circuit = TkCircuit(configuration)
@circuit.run
def main ():
    
    # now just write the code you would use on a real Raspberry Pi
    
    from gpiozero import LED, Button
    from time import sleep
    
    led1 = LED(21)
    led1.blink()
    
    def button_pressed():
        print("button pressed!")
        led2.toggle()
    
    led2 = LED(22)
    button = Button(11)
    button.when_pressed = button_pressed
    
    while True:
        sleep(0.1)

```

You could also initialize the circuit in a function inside a separate Python file, to hide it from students.

Check more sample code files in `docs/examples`.


## Instalation

Download/clone this repository, open your Terminal, navigate to tkgpio's root folder, and use PyPI:

```bash
pip install .
```

I'll upload it to PyPI later on, after a few tweaks.
