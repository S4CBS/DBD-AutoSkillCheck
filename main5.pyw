# Default imports
import PyQt5
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import (QTabWidget, QWidget, QLabel, QPushButton, QTextBrowser,
                             QCheckBox, QMainWindow, QApplication)
from PyQt5.QtGui import QFont, QIcon
from threading import Thread
from multiprocessing import Process, Value, Array, freeze_support
from ctypes import c_bool, c_int
from pynput.keyboard import KeyCode, Listener, Key
import configparser
import sys
import os
# Importing script functions
import pygame
from pynput.keyboard import KeyCode
from utility import Utility
from auto_skillcheck import auto_skillcheck
from get_target_info import get_target_window_info
from configurate_monitor import ConfigureMonitor


class TargetInfoThread(QThread):
    update_target_info = pyqtSignal(bool, list)

    def __init__(self, gti_toggle):
        super().__init__()
        self.gti_toggle = gti_toggle

    def run(self):
        window_rect = [0, 0, 0, 0]  # Пример: [x, y, width, height]
        is_target_active = False

        while True:
            if self.gti_toggle.value:
                # Получаем информацию о целевом окне
                is_target_active, window_rect = get_target_window_info()
                self.update_target_info.emit(is_target_active, window_rect)


class DeadByDaylightScript(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        pygame.mixer.init()
        # Needed for windows (multiprocessing cause to spawn new window)
        freeze_support()
        # Init configparser
        self.config = configparser.ConfigParser()
        # Init Utility
        self.utility = Utility()
        # Init parent gui
        self.init_gui()
        # Script functions toggle
        self.gti_toogle = Value(c_bool, 1)  # get target info
        self.asc_toggle = Value(c_bool, 0)  # auto skillcheck
        self.sound_on = pygame.mixer.Sound('Sounds/ON.mp3')
        self.sound_off = pygame.mixer.Sound('Sounds/OFF.mp3')
        self.sound_doctor_mode_on = pygame.mixer.Sound('Sounds/ON_DC.mp3')
        self.sound_doctor_mode_off = pygame.mixer.Sound('Sounds/OFF_DC.mp3')
        # Load keycodes (params for script's functions)
        self.asc_keycode = None
        # Screen capture zones
        self.asc_monitor = None
        self.aw_monitor_hand = None
        self.aw_monitor_arrow = None
        # Load config
        self.__load_config()
        # Sync variables, information about target window
        self.is_target_active = Value(c_bool, False)  # true if target window foregrounded
        self.window_rect = Array(c_int, range(4))  # target window rect (from win32gui)
        # Starting necessary thread to get information about target window
        self.get_target_info_thread = Thread(target=get_target_window_info,
                                             args=(self.gti_toogle, self.is_target_active,
                                                   self.window_rect))
        self.get_target_info_thread.start()
        listener = Listener(on_press=self.on_key_press)
        listener.start()

    def on_key_press(self, key):
        if key == self.on_off_keycode:
            self.asc_checkbox.setChecked(not self.asc_checkbox.isChecked())
        elif key == self.on_off_keycode_doctor_mode:
            self.doctor_mode_checkbox.setChecked(not self.doctor_mode_checkbox.isChecked())

    def on_asc_checkbox_changed(self):
        self.asc_toggle = self.asc_checkbox.isChecked()
        if self.asc_toggle:
            self.log_browser.append("[+] Auto SkillCheck -> ON")
            pygame.mixer.Sound.play(self.sound_on)
        else:
            self.log_browser.append("[+] Auto SkillCheck -> OFF")
            pygame.mixer.Sound.play(self.sound_off)

    def init_gui(self) -> None:
        def __set_pointer_size(widget: PyQt5.QtWidgets, size: int) -> None:
            """Sets pointer size of text
            Args:
                widget (PyQt5.QtWidgets): like QCheckBox
                size (int): size of pointer (px)
            """
            font = QFont()
            font.setPointSize(size)
            widget.setFont(font)

        self.setFixedSize(520, 180)
        self.setWindowTitle("DBD Script by S4CBS")
        self.setWindowIcon(QIcon('icon.ico'))
        self.tabs = QTabWidget(self)
        self.tabs.resize(302, 170)
        self.asc_tab = QWidget()
        self.am1_tab = QWidget()
        self.aw_tab = QWidget()
        self.tabs.addTab(self.asc_tab, "Auto SkillCheck")
        # Auto SkillCheck
        # Checkbox
        self.asc_checkbox = QCheckBox(self.asc_tab)
        __set_pointer_size(self.asc_checkbox, 10)
        self.asc_checkbox.setText("Auto SkillCheck")
        self.asc_checkbox.adjustSize()
        self.asc_checkbox.move(10, 10)
        # Change Keybind
        self.asc_keybind_lbl = QLabel(self.asc_tab)
        __set_pointer_size(self.asc_keybind_lbl, 10)
        self.asc_keybind_lbl.setText("Change Keybind:")
        self.asc_keybind_lbl.adjustSize()
        self.asc_keybind_lbl.move(10, 40)
        self.asc_keybind_btn = QPushButton(self.asc_tab)
        self.asc_keybind_btn.resize(60, 25)
        self.asc_keybind_btn.move(115, 35)
        # Change Keybind (Для кнопки активации и деактивации в игре)
        self.asc_keybind_lbl_ = QLabel(self.asc_tab)
        __set_pointer_size(self.asc_keybind_lbl_, 10)
        self.asc_keybind_lbl_.setText("ON/OFF KEY:")
        self.asc_keybind_lbl_.adjustSize()
        self.asc_keybind_lbl_.move(200, 10)
        self.asc_keybind_btn_ = QPushButton(self.asc_tab)
        self.asc_keybind_btn_.resize(60, 25)
        self.asc_keybind_btn_.move(210, 35)
        # Configurate monitor
        self.asc_monitor_lbl = QLabel(self.asc_tab)
        __set_pointer_size(self.asc_monitor_lbl, 10)
        self.asc_monitor_lbl.setText("Configure screen capture zone: ")
        self.asc_monitor_lbl.adjustSize()
        self.asc_monitor_lbl.move(10, 70)
        self.asc_monitor_btn = QPushButton(self.asc_tab)
        self.asc_monitor_btn.resize(60, 25)
        self.asc_monitor_btn.move(10, 90)
        self.asc_monitor_btn.setText("Configure")
        self.asc_std_monitor_btn = QPushButton(self.asc_tab)
        self.asc_std_monitor_btn.resize(60, 25)
        self.asc_std_monitor_btn.move(75, 90)
        self.asc_std_monitor_btn.setText("Default")
        # Замена кнопок Doctor Mode и Not Doctor Mode на чекбокс
        self.doctor_mode_checkbox = QCheckBox(self.asc_tab)
        __set_pointer_size(self.doctor_mode_checkbox, 10)
        self.doctor_mode_checkbox.setText("Doctor Mode")
        self.doctor_mode_checkbox.adjustSize()
        self.doctor_mode_checkbox.move(10, 120)
        self.doctor_mode_checkbox.stateChanged.connect(self.on_doctor_mode_checkbox_changed)
        # Connecting
        self.asc_keybind_btn.clicked.connect(lambda x: self.__change_keybind_btn_handle("AutoSkillCheck", "keycode"))
        self.asc_checkbox.stateChanged.connect(lambda x: self.__checkbox_handle(self.asc_toggle,
                                                                                Process,
                                                                                auto_skillcheck,
                                                                                self.asc_toggle,  # args
                                                                                self.is_target_active,
                                                                                self.window_rect,
                                                                                self.asc_monitor,
                                                                                self.asc_keycode,
                                                                                self.get_DoctorModeInteger(),
                                                                                self.get_SleepValueDoctorMode(),
                                                                                self.get_HeightWidth(),
                                                                                self.get_DefaultSleep()))
        self.asc_monitor_btn.clicked.connect(lambda x: self.__change_monitor_btn_handle("AutoSkillCheck", "monitor"))
        self.asc_std_monitor_btn.clicked.connect(lambda x: self.update_config("AutoSkillCheck", "monitor", "default"))
        #Connecting
        self.asc_keybind_btn_.clicked.connect(lambda x: self.__change_keybind_btn_handle("ON/OFF AutoSkC", "keycode"))
        # Logging
        self.log_lbl = QLabel(self)
        self.log_lbl.setText("Logging")
        self.log_lbl.adjustSize()
        self.log_lbl.move(390, 5)
        self.log_browser = QTextBrowser(self)
        self.log_browser.resize(208, 132)
        self.log_browser.move(305, 20)
        self.show()

    def on_doctor_mode_checkbox_changed(self):
        if self.doctor_mode_checkbox.isChecked():
            self.log_browser.append("[+] Doctor Mode -> ON")
            self.update_config("Doctor Mode", "value", "1")
            pygame.mixer.Sound.play(self.sound_doctor_mode_on)
        else:
            self.log_browser.append("[-] Doctor Mode -> OFF")
            self.update_config("Doctor Mode", "value", "0")
            pygame.mixer.Sound.play(self.sound_doctor_mode_off)

    def get_DoctorModeInteger(self):
        self.config.read(f"{os.getcwd()}\\config.ini")
        dcm = self.config.get("Doctor Mode", "value")
        return int(dcm)

    def get_SleepValueDoctorMode(self):
        self.config.read(f"{os.getcwd()}\\config.ini")
        slp = self.config.get("Doctor Mode", "sleepvalue")
        return float(slp)

    def get_DefaultSleep(self):
        self.config.read(f"{os.getcwd()}\\config.ini")
        slp = self.config.get("AutoSkillCheck", "sleepvalue")
        return float(slp)

    def get_HeightWidth(self):
        self.config.read(f"{os.getcwd()}\\config.ini")
        height = self.config.get("Doctor Mode", "height")
        width = self.config.get("Doctor Mode", "width")
        return int(height), int(width)

    def on_update_target_info(self, is_active, window_rect):
        # Обновляем информацию о цели на GUI
        if is_active:
            self.log_browser.append(f"[+] Target window active: {window_rect}")
        else:
            self.log_browser.append("[-] Target window not active")

    def __checkbox_handle(self, toggle: bool, launch_method: object, function: object, *args, **kwargs) -> None:
        """Accepts a function enable signal from checkboxes and (starts / disables) (processes / threads)
        Args:
            toggle (bool): On / Off toggle
            launch_method (object): Process or Thread object like `multiprocessing.Process`
            function (object): function that's need to be started / stopped
        """
        sender = self.sender()
        if sender.isChecked():
            toggle.value = 1
            launch_method(target=function, args=args, kwargs=kwargs).start()
            self.log_browser.append(f"[+] {sender.text()} -> ON")
            pygame.mixer.Sound.play(self.sound_on)  # Воспроизведение звука включения
        else:
            toggle.value = 0
            self.log_browser.append(f"[+] {sender.text()} -> OFF")
            pygame.mixer.Sound.play(self.sound_off)  # Воспроизведение звука выключения

    def __change_keybind_btn_handle(self, partition: str, param: str) -> None:
        """Changes keybind (via updating config.ini file) when the keybind button is clicked
        NEED TO COMPLETE
        WHAT NEEDED:
        1. Add processing  - if several buttons are pressed at the same time
        Args:
            partition (str): partition of cfg
            param (str): param of selected partition
        """
        self.log_browser.append("[=] Waiting for a button...")
        sender = self.sender()
        sender.setStyleSheet("background-color: #8A2BE2; color: #FFF;")
        self.__change_btn_name(sender, "Waiting...", False)

        def on_press(key):
            try:
                self.update_config(partition, param, key)
                return False
            except:
                self.log_browser.append("[ERROR] An error occured while changing the button")
                self.update_config(partition, param, "None")
                return False

        listener = Listener(on_press=on_press)
        listener.start()

    def __change_monitor_btn_handle(self, partition: str, param: str) -> None:
        file_path = self.utility.get_file_path(self)
        # Init child configure window
        if file_path:
            self.configure_window = ConfigureMonitor(file_path, partition, param, self)
            self.configure_window.show()

    def __create_config(self) -> None:
        """Creates a config file
        Runs if no config.ini file was found or need to be replaced
        """
        self.config.add_section("AutoSkillCheck")
        self.config.set("AutoSkillCheck", "keycode", "Key.alt_l")  # alt_l is default keybind
        self.config.set("AutoSkillCheck", "monitor", "default")
        self.config.set("AutoSkillCheck", "sleepvalue", "0.0")
        self.config.add_section("ON/OFF AutoSkC")
        self.config.set("ON/OFF AutoSkC", "keycode", "Key.insert")  # insert is default keybind
        self.config.add_section("Doctor Mode")
        self.config.set("Doctor Mode", "value", "0")
        self.config.set("Doctor Mode", "keycode", "Key.home")
        self.config.set("Doctor Mode", "sleepvalue", "0.0000008")
        self.config.set("Doctor Mode", "height", "500")
        self.config.set("Doctor Mode", "width", "500")
        with open(f"{os.getcwd()}\\config.ini", "w") as config_file:
            self.config.write(config_file)

    def __load_config(self) -> None:
        """Loads settings from a configuration file
        """
        self.log_browser.append("[+] Loading config...")
        config_file_path = os.getcwd() + "\\config.ini"
        if not os.path.exists(config_file_path):
            self.log_browser.append("[=] Config not exists, creating new one")
            self.__create_config()
        # Here loading settings from config file
        try:
            self.config.read(f"{os.getcwd()}\\config.ini")
            #Auto SkillCheck
            self.asc_keycode = self.__read_keycode(self.config.get("AutoSkillCheck", "keycode"))
            self.__change_btn_name(self.asc_keybind_btn, self.asc_keycode)
            self.asc_monitor = self.__read_monitor(
                self.config.get("AutoSkillCheck", "monitor"))  # Make a dict() from str object
            # ON/OFF AutoSkC
            self.on_off_keycode = self.__read_keycode(self.config.get("ON/OFF AutoSkC", "keycode"))
            self.__change_btn_name(self.asc_keybind_btn_, self.on_off_keycode)
            # Doctor Mode
            self.on_off_keycode_doctor_mode = self.__read_keycode(self.config.get("Doctor Mode", "keycode"))
            if self.get_DoctorModeInteger() == 1:
                self.doctor_mode_checkbox.setChecked(True)
            self.log_browser.append("[+] Config loaded!")
        except:
            self.log_browser.append("[WARN] Config is uncorrect! Loading the standard settings file...")
            self.config = configparser.ConfigParser()
            self.__create_config()
            self.__load_config()

    def update_config(self, partition: str, param: str, value: str) -> None:
        """Updates the config file and calls the `self.__load_config()` function
        Args:
            partition (str): Partition of cfg file
            param (str): Parameter of cfg file
            value (str): The value to be written
        """
        self.config.set(partition, param, str(value).replace("'", ""))
        with open(f"{os.getcwd()}\\config.ini", "w") as config_file:
            self.config.read(f"{os.getcwd()}\\config.ini")
            self.config.write(config_file)
            self.log_browser.append(f"[+] [{param}] of [{partition}] has been set to [{value}]")
            self.__load_config()

    def __read_keycode(self, keycode_str: str) -> object:
        """Takes a string keycode object and returns it as an object of pynput.keyboard
        Args:
            keycode_str (str): keycode thats need to be converted in pynput.keyboard object
        Returns:
            object: pynput.keyboard object
        """
        keycode = None
        try:
            keycode = eval(keycode_str)
            # self.log_browser.append("[DEBUG] Config (keycode) has <Key> like keycode")
            return keycode
        except NameError:
            try:
                if len(keycode_str) == 1:
                    keycode = KeyCode.from_char(keycode_str)
                    # self.log_browser.append("[DEBUG] Config (keycode) has <KeyCode> like keycode")
                    return keycode
                else:
                    self.log_browser.append(
                        "[ERROR] Config (keycode) multiple characters found, delete config file and restart the program")
            except:
                self.log_browser.append("[ошибочка] не пиши гавно в конфиге")
                self.__create_config()
                self.__load_config()
        except:
            self.log_browser.append("[ERROR] Can't load config (keycode) - unknown type of keycode")
            self.__create_config()
            self.__load_config()

    def __read_monitor(self, monitor_str: str) -> dict:
        try:
            try:
                monitor = eval(monitor_str)
                return monitor
            except NameError:
                return monitor_str
        except:
            self.log_browser.append("[ERROR] Incorrect type of monitor (config.ini). Monitor has been set to default")
            return "default"

    def __change_btn_name(self, btn_object: object, name: str, use_keynames: bool = True) -> None:
        """Changes the name of the button
        Args:
            btn_object (object): The button whose name you want to change
            name (str): New name of button
            use_keynames (bool, optional): If necessary to use keynames dict(). Defaults to True.
        """
        keynames = {
            "Key.alt": "Alt",
            "Key.alt_gr": "AltGr",
            "Key.alt_l": "Left Alt",
            "Key.alt_r": "Right Alt",
            "Key.backspace": "BSPACE",
            "Key.caps_lock": "CapsLock",
            "Key.cmd": "Win",
            "Key.cmd_l": "Left Win",
            "Key.cmd_r": "Right Win",
            "Key.ctrl": "Ctrl",
            "Key.ctrl_l": "Left Ctrl",
            "Key.ctrl_r": "Right Ctrl",
            "Key.delete": "Delete",
            "Key.down": "Down",
            "Key.end": "End",
            "Key.enter": "Enter",
            "Key.esc": "Esc",
            "Key.f1": "F1",
            "Key.f2": "F2",
            "Key.f3": "F3",
            "Key.f4": "F4",
            "Key.f5": "F5",
            "Key.f6": "F6",
            "Key.f7": "F7",
            "Key.f8": "F8",
            "Key.f9": "F9",
            "Key.f10": "F10",
            "Key.f11": "F11",
            "Key.f12": "F12",
            "Key.f13": "F13",
            "Key.f14": "F14",
            "Key.f15": "F15",
            "Key.f16": "F16",
            "Key.f17": "F17",
            "Key.f18": "F18",
            "Key.f19": "F19",
            "Key.f20": "F20",
            "Key.home": "Home",
            "Key.insert": "INS",
            "Key.left": "Left",
            "Key.media_next": "Media NXT",
            "Key.media_play_pause": "Media Play",
            "Key.media_previous": "Media Prev",
            "Key.media_volume_down": "Vol Down",
            "Key.media_volume_mute": "Vol Mute",
            "Key.media_volume_up": "Vol Up",
            "Key.menu": "Menu",
            "Key.num_lock": "NumLock",
            "Key.page_down": "PD",
            "Key.page_up": "PU",
            "Key.pause": "Pause",
            "Key.print_screen": "PS",
            "Key.right": "Right",
            "Key.scroll_lock": "SL",
            "Key.shift": "Shift",
            "Key.shift_l": "Left Shift",
            "Key.shift_r": "Right Shift",
            "Key.space": "Space",
            "Key.tab": "Tab",
            "Key.up": "Up"
        }
        try:
            name = str(name).replace("'", "")
            if use_keynames:
                btn_object.setStyleSheet("")  # Set default style of btn_object
                keyname = keynames.get(name)
                if keyname == None:
                    keyname = name.upper()
                btn_object.setText(keyname)
            else:
                btn_object.setText(name)
        except:
            self.log_browser.append(f"[ERROR] Can't change name of btn ({btn_object})")
            btn_object.setText(":(")

    def __turn_off_tasks(self) -> None:
        """Turn off all tasks
        """
        self.gti_toogle.value = 0
        self.asc_toggle.value = 0

    def closeEvent(self, event) -> None:
        self.listener.stop()
        self.target_info_thread.quit()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ui = DeadByDaylightScript()
    sys.exit(app.exec_())
