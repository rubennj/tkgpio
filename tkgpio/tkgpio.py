from .base import TkDevice, SingletonMeta
from .base import PreciseMockTriggerPin, PreciseMockFactory, PreciseMockChargingPin
from gpiozero import Device
from gpiozero.pins.mock import MockPWMPin
from PIL import ImageEnhance, Image, ImageDraw, ImageFont, ImageTk
from sounddevice import play, stop
import numpy
import scipy.signal
from tkinter import Tk, Frame, Label, Button, Scale, HORIZONTAL, VERTICAL, CENTER
from threading import Thread, Timer
from sys import path, exit
from pathlib import Path
from functools import partial
from math import sqrt
import os
      
      
class TkCircuit(metaclass=SingletonMeta):
    def __init__(self, setup):
        Device.pin_factory = PreciseMockFactory(pin_class=MockPWMPin)
        
        path.insert(0, str(Path(__file__).parent.absolute()))
        
        default_setup = {
            "name": "Virtual GPIO",
            "width": 500, "height": 500,
            "leds":[], "buzzers":[], "buttons":[],
            "lcds":[],
            "motion_sensors": [],
            "distance_sensors": [],
            "light_sensors": [],
            "infrared_receiver": None,
            "infrared_emitter": None
        }
        
        default_setup.update(setup)
        setup = default_setup
                
        self._root = Tk()
        self._root.title(setup["name"])
        self._root.geometry("%dx%d" % (setup["width"], setup["height"]))
        self._root.resizable(False, False)
        self._root["background"] = "white"
        self._root.protocol("WM_DELETE_WINDOW", self._on_closing)
        self._root.tk.call("tk", "scaling", 1.0)
        
        self._outputs = []
        self._outputs += [self.add_device(TkLED, parameters) for parameters in setup["leds"]]
        self._outputs += [self.add_device(TkBuzzer, parameters) for parameters in setup["buzzers"]]
        
        self._lcds = [self.add_device(TkLCD, parameters) for parameters in setup["lcds"]]
        
        for parameters in setup["buttons"]:
            self.add_device(TkButton, parameters)
            
        for parameters in setup["distance_sensors"]:
            self.add_device(TkDistanceSensor, parameters)
            
        for parameters in setup["light_sensors"]:
            self.add_device(TkLightSensor, parameters)
            
        for parameters in setup["motion_sensors"]:
            self.add_device(TkMotionSensor, parameters)
        
        if setup["infrared_receiver"] != None:
            self.add_device(TkInfraredReceiver, setup["infrared_receiver"])
             
        if setup["infrared_emitter"] != None:
            self.add_device(TkInfraredEmitter, setup["infrared_emitter"])
            
    def add_device(self, device_class, parameters):
        return device_class(self._root, **parameters)
        
    def run(self, function):
        thread = Thread(target=function, daemon=True)
        thread.start()
        
        self._root.after(10, self._update_outputs)    
        self._root.mainloop()
        
    def _update_outputs(self):
        for output in self._outputs:
            output.update()
            
        self._root.after(10, self._update_outputs)
        
    def update_lcds(self, pins, text):
        for lcds in self._lcds:
            lcds.update_text(pins, text)
            
    def _on_closing(self):
        exit()
        
        
class TkLCD(TkDevice):
    _image = None
    _photo_image = None
    
    def __init__(self, root, x, y, name, pins, columns, lines):
        super().__init__(root, x, y, name)
        self._redraw()
     
        self._pins = pins
        self._columns = columns
        self._lines = lines
            
        self._label = Label(root)
        self._label.place(x=x, y=y)
        
        self.update_text(self._pins, "")
        
    def update_text(self, pins, text):
        MARGIN = 8
        FONT_SIZE = 17
        CHAR_WIDTH = 12
        CHAR_HEIGHT = 16
        CHAR_X_GAP = 3
        CHAR_Y_GAP = 5
        
        image_width = MARGIN * 2 + self._columns * (CHAR_WIDTH) + (self._columns - 1) * CHAR_X_GAP
        image_height = MARGIN * 2 + self._lines * (CHAR_HEIGHT) + (self._lines - 1) * CHAR_Y_GAP
        
        if pins == self._pins:
            image = Image.new('RGB', (image_width, image_height), color="#82E007")
 
            current_folder = os.path.dirname(__file__)
            font_path = os.path.join(current_folder, "resources/fonts/hd44780.ttf")
            font = ImageFont.truetype(font_path, FONT_SIZE)
            d = ImageDraw.Draw(image)
            
            x = MARGIN
            for j in range(0, self._columns):
                y = MARGIN
                for i in range(0, self._lines):
                    d.rectangle((x, y, x+CHAR_WIDTH, y+CHAR_HEIGHT), fill ="#72D000")
                    y += (CHAR_Y_GAP + CHAR_HEIGHT)
                    
                x += (CHAR_X_GAP + CHAR_WIDTH)
                    
            x = MARGIN
            y = MARGIN
            line = 1
            column = 1
            for character in text:
                if character == "\n":
                    y += (CHAR_Y_GAP + CHAR_HEIGHT)
                    x = MARGIN
                    line += 1
                    column = 1
                else:
                    if line <= self._lines and column <= self._columns:
                        d.text((x,y), character, font=font, fill="black")
                        
                    x += (CHAR_X_GAP + CHAR_WIDTH)
                    column += 1
            
            self._photo_image = ImageTk.PhotoImage(image)
            
            self._label.configure(image = self._photo_image)
            self._redraw()
            self._root.update()
        
        
class TkBuzzer(TkDevice):
    SAMPLE_RATE = 44000
    PEAK = 0.1
    DUTY_CICLE = 0.5
    
    def __init__(self, root, x, y, name, pin, frequency=440):
        super().__init__(root, x, y, name)
        
        self._pin = Device.pin_factory.pin(pin)
        self._previous_state = None
        
        self._set_image_for_state("buzzer_on.png", "on", (50, 33))
        self._set_image_for_state("buzzer_off.png", "off", (50, 33))
        self._create_main_widget(Label, "off")
        
        if frequency != None:
            n_samples = self.SAMPLE_RATE
            t = numpy.linspace(0, 1, int(500 * 440/frequency), endpoint=False)
            wave = scipy.signal.square(2 * numpy.pi * 5 * t, duty=self.DUTY_CICLE)
            wave = numpy.resize(wave, (n_samples,))
            self._sample_wave = (self.PEAK / 2 * wave.astype(numpy.int16))
        else:
            self._sample_wave = numpy.empty(0)
        
    def update(self):
        if self._previous_state != self._pin.state:
            if self._pin.state == True:
                self._change_widget_image("on")
                # if len(self._sample_wave) > 0:
                    # play(self._sample_wave, self.SAMPLE_RATE, loop=True)
            else:
                self._change_widget_image("off")
                # if len(self._sample_wave) > 0:
                    # stop()
            
            self._previous_state = self._pin.state
            
            self._redraw()
    

class TkLED(TkDevice):
    on_image = None
    
    def __init__(self, root, x, y, name, pin):
        super().__init__(root, x, y, name)
        
        self._pin = Device.pin_factory.pin(pin)
        
        self._previous_state = None
        
        TkLED.on_image = self._set_image_for_state("led_on.png", "on", (30, 30))
        self._set_image_for_state("led_off.png", "off", (30, 30))
        self._create_main_widget(Label, "off")
        
    def update(self):
        if self._previous_state != self._pin.state:
            if isinstance(self._pin.state, float):
                converter = ImageEnhance.Color(TkLED.on_image)
                desaturated_image = converter.enhance(self._pin.state)
                self._change_widget_image(desaturated_image)
            elif self._pin.state == True:
                self._change_widget_image("on")
            else:
                self._change_widget_image("off")
             
            self._previous_state = self._pin.state
            
            self._redraw()
        
        
class TkButton(TkDevice):
    def __init__(self, root, x, y, name, pin):
        super().__init__(root, x, y, name)
        
        self._pin = Device.pin_factory.pin(pin)
        
        self._set_image_for_state("button_pressed.png", "on", (30, 30))
        self._set_image_for_state("button_released.png", "off", (30, 30))
        self._create_main_widget(Button, "off")
        self._widget.config(borderwidth=0,highlightthickness = 0,background="white")
        self._widget.bind("<ButtonPress>", self._on_press)
        self._widget.bind("<ButtonRelease>", self._on_release)
        
    def _on_press(self, botao):
        self._change_widget_image("on")
        
        thread = Thread(target=self._change_pin, daemon=True, args=(True,))
        thread.start()

    def _on_release(self, botao):
        self._change_widget_image("off")
        
        thread = Thread(target=self._change_pin, daemon=True, args=(False,))
        thread.start()
        
    def _change_pin(self, is_press):
        if is_press:
            self._pin.drive_low()
        else:
            self._pin.drive_high()
          
            
class TkMotionSensor(TkDevice):
    def __init__(self, root, x, y, name, pin, detection_radius=50, delay_duration=5, block_duration=3):
        super().__init__(root, x, y, name)
        
        self._pin = Device.pin_factory.pin(pin)
        
        self._detection_radius = detection_radius
        self._delay_duration = delay_duration
        self._block_duration = block_duration
        
        self._motion_timer = None
        self._block_timer = None
        
        self._set_image_for_state("motion_sensor_on.png", "motion", (80, 60))
        self._set_image_for_state("motion_sensor_off.png", "no motion", (80, 60))
        self._set_image_for_state("motion_sensor_wait.png", "wait", (80, 60))
        self._create_main_widget(Label, "no motion")
        
        root.bind('<Motion>', self._motion_detected)
        
    def _motion_detected(self, event):
        x_pointer = self._root.winfo_pointerx() - self._root.winfo_rootx()
        y_pointer = self._root.winfo_pointery() - self._root.winfo_rooty()
        x_center = self._widget.winfo_x() + self._widget.winfo_width() / 2
        y_center = self._widget.winfo_y() + self._widget.winfo_height() / 2
        distance = sqrt(pow(x_pointer - x_center, 2) + pow(y_pointer - y_center, 2))
        
        if distance < self._detection_radius and self._block_timer == None:
            if self._motion_timer == None:
                self._change_widget_image("motion")
            else:
                self._motion_timer.cancel()
                
            self._pin.drive_high()
                 
            self._motion_timer = Timer(self._delay_duration, self._remove_detection)
            self._motion_timer.start()
            
    def _remove_detection(self):
        self._pin.drive_low()
        self._change_widget_image("wait")
        
        self._motion_timer = None
        
        self._block_timer = Timer(self._block_duration, self._remove_block)
        self._block_timer.start()
    
    def _remove_block(self):
        self._change_widget_image("no motion")
        self._block_timer = None
            
            
class TkDistanceSensor(TkDevice):
    def __init__(self, root, x, y, name, trigger_pin, echo_pin, min_distance=0, max_distance=50):
        super().__init__(root, x, y, name)
        
        self._echo_pin = Device.pin_factory.pin(echo_pin)
        self._trigger_pin = Device.pin_factory.pin(trigger_pin,
            pin_class=PreciseMockTriggerPin, echo_pin=self._echo_pin, echo_time=0.004)
        
        self._echo_pin._bounce = 0
        self._trigger_pin._bounce = 0
        
        self._set_image_for_state("distance_sensor.png", "normal", (86, 50))
        self._create_main_widget(Label, "normal")
        
        self._scale = Scale(root, from_=min_distance, to=max_distance,
            orient=HORIZONTAL, command=self._scale_changed, sliderlength=20, length=150, highlightthickness = 0, background="white")
        self._scale.place(x=x+100, y=y)
        self._scale.set(round((min_distance + max_distance) / 2))
        self._scale_changed(self._scale.get())
        
    def _scale_changed(self, value):
        speed_of_sound = 343.26 # m/s
        distance = float(value) / 100 # cm -> m
        self._trigger_pin.echo_time = distance * 2 / speed_of_sound
      
      
class TkLightSensor(TkDevice):
    def __init__(self, root, x, y, name, pin):
        super().__init__(root, x, y, name)
        
        self._pin = Device.pin_factory.pin(pin, pin_class=PreciseMockChargingPin)
        
        self._scale = Scale(root, from_=0, to=90, showvalue=0,
            orient=VERTICAL, command=self._scale_changed, sliderlength=20, length=150, highlightthickness = 0, background="white")
        self._scale.place(x=x+90, y=y)
        self._scale.set(30)
        self._scale_changed(self._scale.get())
        
        self._set_image_for_state("light_sensor.png", "normal", (75, 150))
        self._create_main_widget(Label, "normal")
        
    def _scale_changed(self, value):
        self._pin.charge_time = float(value) / 10000
            
            
class TkInfraredReceiver(TkDevice, metaclass=SingletonMeta):

    def __init__(self, root, x, y, name, config, remote_control):
        super().__init__(root, x, y, name)
        
        remote = remote_control
        
        frame = Frame(root, bg = remote["color"], width = remote["width"], height = remote["height"])
        frame.place(x=x, y=y)
        
        self._config = config
        self._key_codes = []
        self._pressed_key_codes = []
        
        for i in range(0, len(remote["key_rows"])):
            row = remote["key_rows"][i]
            for j in range(0, len(row["buttons"])):
                button_setup = row["buttons"][j]
                if button_setup != None:
                    code = button_setup.get("code", "KEY_" + button_setup["name"])
                    self._key_codes.append(code)
                    
                    command = partial(self._key_press, code)
                    
                    button = Button(frame, text=button_setup["name"],
                                    width=remote["key_width"], height=remote["key_height"],
                                    command=command,
                                    justify=CENTER, highlightbackground=remote["color"])
                    button.grid(row=i, column=j, padx=8, pady=8)
        
        frame.configure(width = remote["width"], height = remote["height"])
    
    def config_name(self):
        return self._config
    
    def clear_codes(self):
        self._pressed_key_codes = []
    
    def get_next_code(self):
        if len(self._pressed_key_codes) == 0:
            return []
        else:
            return [self._pressed_key_codes.pop(0)]
    
    def _key_press(self, code):
        self._pressed_key_codes.append(code)
        
        
class TkInfraredEmitter(TkDevice, metaclass=SingletonMeta):
    def __init__(self, root, x, y, name, remote_controls):
        super().__init__(root, x, y, name)
        
        self._set_image_for_state("emitter_on.png", "on", (50, 30))
        self._set_image_for_state("emitter_off.png", "off", (50, 30))
        self._create_main_widget(Label, "off")
        
        self._remote_controls = remote_controls
        
        self._timer = None
        
    def list_remotes(self, remote):
        return self._remote_controls.keys()
    
    def list_codes(self, remote):
        valid_codes = self._remote_controls.get(remote, None)
        
        if valid_codes == None:
             print("\x1b[1;37;41m" + remote + ": INVALID REMOTE CONTROL!" + "\x1b[0m")
             
        return valid_codes
        
    def send_once(self, remote, codes, count):
        valid_codes = self.list_codes(remote)
        if valid_codes == None:
            return
        
        has_valid_code = False
        for code in codes:
            if code in valid_codes:
                print("\x1b[1;37;42m" + code + " of remote \"" + remote + "\" transmitted!" + "\x1b[0m")
                has_valid_code = True
            else:
                print("\x1b[1;37;41m" + code + ": INVALID CODE FOR REMOTE \"" + remote +  "\"!" + "\x1b[0m")
                
        if has_valid_code:
            if self._timer != None:
                self._timer.cancel()
                
            self._change_widget_image("on")
                
            self._timer = Timer(1, self._turn_off_emitter).start()
            
    def _turn_off_emitter(self):
        self._change_widget_image("off")
        self._timer = None
