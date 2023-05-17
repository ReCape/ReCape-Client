import shutil
import kivy
import requests
kivy.require('2.1.0')

from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.popup import Popup
from kivy.factory import Factory
import threading
from kivy.clock import Clock
from kivy.properties import ObjectProperty, StringProperty
from kivy.lang import Builder

from recape_api import API

import os
import sys
from kivy.resources import resource_add_path, resource_find

import mojang

# These are to make sure they get picked up by PyInstaller
import dns
import installer

mojangAPI = mojang.API()

DEBUG = os.path.exists(".debug")

class PopupBox(Popup):
    pop_up_text = ObjectProperty()
    def set_popup_text(self, p_message):
        self.pop_up_text.text = p_message
    def set_popup_title(self, text):
        self.title = text
    def set_can_dismiss(self, is_enabled):
        self.dismiss_button.visible = is_enabled
    def set_dismiss_callback(self, callback):
        self.dismiss_button.on_release = callback


class Cape(GridLayout):
    text = StringProperty('')
    source = StringProperty('')
    type = StringProperty('')
    pass

class Model(GridLayout):
    text = StringProperty('')
    activated = ObjectProperty(False)
    pass

class LoadDialog(FloatLayout):
    load = ObjectProperty(None)
    cancel = ObjectProperty(None)
    filters = ObjectProperty([])

class ReCape(App):

    loadfile = ObjectProperty(None)
    text_input = ObjectProperty(None)

    def dismiss_popup(self):
        self._popup.dismiss()

    def show_load(self, onload, filters=[]):
        content = LoadDialog(load=onload, cancel=self.dismiss_popup, filters=filters)
        self._popup = Popup(title="Load file", content=content,
                            size_hint=(0.9, 0.9))
        self._popup.open()

    def make_popup_error(self, error: Exception):
        self.pop_up.set_popup_text("An error occured whilst doing that: " + str(error))
        self.pop_up.set_popup_title("Something went horribly wrong")
        self.pop_up.set_can_dismiss(True)

        if DEBUG:
            raise error
    
    def make_popup_success(self, text, restart):
        self.pop_up.set_popup_text(text)
        self.pop_up.set_popup_title("Finished")
        self.pop_up.set_can_dismiss(True)

        if restart:
            self.pop_up.set_dismiss_callback(self.restart)
        else:
            self.pop_up.set_dismiss_callback(self.pop_up.dismiss)

    def show_popup(self, text, can_dismiss):
        self.pop_up = Factory.PopupBox()
        self.pop_up.set_popup_text(text)
        self.pop_up.set_popup_title("Something's up")
        self.pop_up.set_can_dismiss(can_dismiss)
        self.pop_up.open()

    def run_with_popup(self, process, text, args, returns_message):
        # Open the pop up
        self.show_popup(text, False)

        # Call some method that may take a while to run.
        # I'm using a thread to simulate this
        Clock.schedule_once(lambda _: threading.Thread(target=self._popup_executor, args=(process, args, returns_message)).start())
    
    def _popup_executor(self, process, args, returns_message):
        try:
            message = process(*args)
            if returns_message:
                if type(message) == list:
                    text = message[0]
                    restart = message[1]
                else:
                    text = message
                    restart = False
                self.make_popup_success(text, restart)
            else:
                self.pop_up.dismiss()
        except Exception as e:
            self.make_popup_error(e)
    
    def add_cape(self):
        self.show_load(self._add_cape, ["*.png"])
    def _add_cape(self, path, filename):
        print(path, filename)
        shutil.copyfile(filename[0], "assets/capes/" + filename[0].split("\\")[-1])
        self.load_capes()
        self.dismiss_popup()
    
    def load_capes(self):
        self.root.ids.capes.clear_widgets()

        add_button = Button(text="Add", height=50, size_hint_y=None)
        add_button.bind(on_release=lambda b: self.add_cape())
        self.root.ids.capes.add_widget(add_button)
        self.root.ids.capes.add_widget(Cape(text="No Cape", source="assets/no-cape.png", type="none", on_release=print))
        self.root.ids.capes.add_widget(Cape(text="Use Cloaks+ Cape", source="assets/cloaks-plus.png", type="cloaksplus"))

        directory = "assets/capes"
        directories = directory.split("/")
        current_dir = []
        for current in directories:
            current_dir.append(current)
            if not os.path.exists("/".join(current_dir)):
                os.mkdir("/".join(current_dir))

        capes = os.listdir(directory)

        for cape in capes:
            if cape.endswith(".png"):
                self.root.ids.capes.add_widget(Cape(text=cape, source=directory + "/" + cape, type="cape"))
    
    def load_models(self):
        self.root.ids.models.clear_widgets()
                    
        add_button = Button(text="Add", height=50, size_hint_y=None)
        add_button.bind(on_release=lambda b: self.add_model())
        save_button = Button(text="Save", height=50, size_hint_y=None)
        save_button.bind(on_release=lambda b: self.save_models())
        self.root.ids.models.add_widget(add_button)
        self.root.ids.models.add_widget(save_button)
        
        config = API.get_config()

        models = API.get_cosmetic_list()

        if not models:
            models = []
        if not config:
            config = {"username": "", "password": ""}

        for model in models:
            print("Adding model...")
            activated = False
            if model in config.keys():
                activated = config[model]
            self.root.ids.models.add_widget(Model(text=model, activated=activated))
    
    def add_model(self):
        self.show_load(self._add_model_config, ["*.cfg"])
    def _add_model_config(self, path, filename):
        self.uploading_model = filename[0]
        self.show_load(self._add_model_texture, ["*.png"])
    def _add_model_texture(self, path, filename):
        self.uploading_texture = filename[0]

        self.run_with_popup(API.upload_model, "Uploading your model...", [self.uploading_model, self.uploading_texture], True)
    
    def save_models(self):
        models = {widget.text: widget.active for widget in self.root.ids.models.walk(restrict=True) if hasattr(widget, "name") and widget.name == "model_checkbox"}
        print(models)

        self.run_with_popup(API.set_models, "Updating your model configuration", [models], True)
        
    def on_start(self):
        show_logged_in_tabs = False
        
        credentials = API.read_credentials()

        if credentials:
            try:
                self.username = mojangAPI.get_username(credentials["uuid"])
            except requests.exceptions.ConnectionError:
                self.username = None
            except mojang.NotFound:
                self.username = None

            if self.username:
            
                valid = API.verify_credentials(credentials["token"], credentials["uuid"], self.username)
                if valid:
                    show_logged_in_tabs = True
        
        if show_logged_in_tabs:
            self.root.remove_widget(self.root.ids.log_in_tab)
        else:
            self.root.remove_widget(self.root.ids.cape_tab)
            self.root.remove_widget(self.root.ids.model_tab)
        
        self.load_capes()
        self.load_models()
    
    def restart(self):
        self.root.clear_widgets()
        Builder.unload_file("layout.kv")
        self.stop()
        return ReCape().run()

    def build(self):

        self.title = "ReCape"
        self.icon = "assets/favicon.ico"
        return Builder.load_file("layout.kv")


if __name__ == '__main__':
    ReCape().run()