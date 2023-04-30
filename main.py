import shutil
import flet as ft
import requests
import os
import json
import webbrowser
import mojang
from installer import Installer
import sys

DEBUG = os.path.exists(".debug")

VERSION = "0.0"

RECAPE_URL = "https://localhost" if DEBUG else "https://recape-server.boyne.dev"
#URL = "http://192.168.1.36:80/"

installer = Installer(RECAPE_URL, DEBUG)

QUOTE = """doodle doot doo, doodle doot doo (do)
i love you
no i don't, yes i do,
is that true?
is love just an illusion?"""

ABOUT = """ReCape Desktop Client v""" + VERSION + """
Created by DedFishy

\"""" + QUOTE + "\""

if DEBUG:
    ABOUT += "\nDebug mode is enabled!"

HELP = ft.Column([
    ft.Text("What is this?", size=20),
    ft.Text("ReCape is a service that allows you to obtain free capes and custom 3D models on any Minecraft client that includes OptiFine."),
    ft.Text("What do you mean by 3D models?", size=20),
    ft.Text("They're custom objects that you can attach to any part of your player's body. They can be like a hat, an armband, an ankle monitor, or anything else you can think of that can be attached to you."),
    ft.Text("What do you mean by cape?", size=20),
    ft.Text("A cape is like a banner that hangs off of your shoulders. They can have custom textures, which is what ReCape allows you to modify. As a side effect, you can modify Elytra textures as well!"),
    ft.Text("How does this work?", size=20),
    ft.Text("There's a file on nearly all computers known as a hosts file. This file contains a list of IP addresses and URLs that map to each other. In layman's terms, it lets you change a website's URL to another website's URL. We utilize this by changing OptiFine's servers (s.optifine.net) to redirect to our server's IP address (where it is on the internet). Then, we host your custom capes so that when OptiFine fetches your cape, it will instead get the cape you uploaded. OptiFine also supports hosting 3D models, so we do that too."),
    ft.Text("Why do you need Administrator access in order to install?", size=20),
    ft.Text("The aforementioned hosts file is protected because malicious programs would be able to cut off your access to the internet using it. ReCape needs to edit this file in order to redirect OptiFine's servers, and it needs administrator access to do so."),
    ft.Text("Can everybody see my custom capes and models?", size=20),
    ft.Text("Due to how ReCape works, other players can only see you cape if they both have ReCape installed themselves and are using OptiFine or anb OptiFine-integrated client."),
    ft.Text("How much does this cost?", size=20),
    ft.Text("ReCape is completely free, and it will stay that way forever. If you appreciate the ReCape project, you will be able to donate as soon as we get that set up.")
])

PATH_PREFIX = ""

controls = {}
model_checks = {}

def add_control(name, control):
    controls[name] = control
    return control

def add_model_check(name, control):
    model_checks[name] = control
    return control

page = None

username = None

mojangAPI = mojang.API()

LOGGED_IN_ONLY_TABS = ["Cape", "Model"]

def unload_logged_in_tabs():
    i = 0
    while i < len(tabs):
        if tabs[i].text in LOGGED_IN_ONLY_TABS:
            tabs.pop(i)
            i -= 1
        
        i += 1

def load_logged_in_page():
    credentials = API.read_credentials()
    
    try:
        username = mojangAPI.get_username(credentials["uuid"])
    except requests.exceptions.ConnectionError:
        username = ""
    
    try:
        result = requests.get(RECAPE_URL + "/authenticate/check_token", headers={"token": credentials["token"], "uuid": credentials["uuid"], "username": username}, verify=not DEBUG)
    except requests.exceptions.ConnectionError:
        confirm_action("Could not connect to ReCape servers. Make sure you have an internet conenction. Check the Discord for downtime notifications.")
        unload_logged_in_tabs()
        return

    result = result.json()

    print(result)

    if result["result"] == "invalid":
        unload_logged_in_tabs()
        return
    account_page = ft.Container(
    ft.Column(
                    [
    
    ft.Text("Account", size=30), 
    ft.Text("You're logged in to ReCape. Nice!", text_align=ft.TextAlign.JUSTIFY),
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER
    ),
    alignment=ft.alignment.center,
    )

    tabs[1].content = account_page
    page.update()

def load_capes():
    controls["cape_grid"].controls = []
    controls["cape_grid"].controls.append(CapeButton("no-cape.png", "No Cape", "none"))
    controls["cape_grid"].controls.append(CapeButton("cloaks-plus.png", "Use Cloaks+ Cape", "cloaksplus"))

    capes = os.listdir(PATH_PREFIX + "assets/capes")

    for cape in capes:
        if cape.endswith(".png"):
            controls["cape_grid"].controls.append(CapeButton("capes/" + cape, cape.replace(".png", ""), cape))

def load_models():
    controls["model_grid"].controls = []
    config = API.get_config()

    models = API.get_cosmetic_list()

    if not models:
        models = []

    for model in models:
        print("Adding model...")
        activated = False
        if model in config.keys():
            activated = config[model]
        controls["model_grid"].controls.append(ModelButton(model, model, activated=activated)) 

def load_cape(cape):
    if cape.files:
        cape = cape.files[0]
        print(cape)
        shutil.copy(cape.path, PATH_PREFIX + "assets/capes/" + cape.name)
        load_capes()
        confirm_action("The cape file \"" + cape.name + "\" has been successfully imported.")
        page.update()

current_model = None
current_texture = None
def load_model_file(model):
    global current_model
    current_model = model
    texture_picker.pick_files("Choose a model texture", allowed_extensions=["png"], allow_multiple=False)

def load_new_model(texture):
    global current_texture
    current_texture = texture

    print(current_model, current_texture)

    if current_model == None and current_texture == None:
        return

    page.dialog = model_settings
    model_settings.open = True
    page.update()

def upload_model():
    if len(controls["model_name"].value) < 3:
        return #TODO: Send a proper message here that the name must be longer

    model_close()

    set_processing_sheet(True, "Sending model to servers...")
    credentials = API.read_credentials()

    files = {}

    files = {"model": open(current_model.files[0].path, "rb"), "texture": open(current_texture.files[0].path, "rb")}  

    try: 
    
        result = requests.post(RECAPE_URL + "/account/upload_cosmetic", headers={"uuid": credentials["uuid"], "token": credentials["token"]}, files=files, verify=not DEBUG)

        result = result.json()

        set_processing_sheet(False)

        if result["status"] == "success":
            confirm_action("Successfully uploaded model files")
        elif result["status"] == "failure":
            confirm_action(result["error"])
        else:
            confirm_action("*shrugs*") # ignorance is bliss
    except Exception as e:
        set_processing_sheet(False)
        confirm_action("An error occurred, and your model could not be uploaded. Check the Discord for downtime information.")
        print(e)

cape_picker = ft.FilePicker(on_result=load_cape)

texture_picker = ft.FilePicker(on_result=load_new_model)
model_picker = ft.FilePicker(on_result=load_model_file)

# Model importing settings screen
def model_close():
    model_settings.open = False
    page.update()

model_settings = ft.AlertDialog(
        modal=True,
        title=ft.Text("Importing model"), 
        content=ft.Text("You're almost ready to get your model!"),
        actions=[
            add_control("model_name", ft.TextField(hint_text="Model Name")),
            ft.TextButton(text="Upload", on_click=lambda e: upload_model()),
            ft.TextButton(text="Cancel", on_click=lambda e: model_close())
        ],
        on_dismiss=lambda e: print("Dialog dismissed!")
    )

class API:
    def read_credentials():
        folder = os.path.expanduser("~") + "/.recape"

        try:
            os.mkdir(folder)
        except FileExistsError:
            pass

        try:
            with open(folder + "/auth.json", "r") as auth:
                data = auth.read()
                data = json.loads(data)
            
            if not "uuid" in data.keys() or not "token" in data.keys():
                return None

            return data
        except Exception as e:
            return None

    def save_credentials(token, uuid):
        folder = os.path.expanduser("~")
        folder += "/.recape"

        try:
            os.mkdir(folder)
        except FileExistsError:
            pass

        with open(folder + "/auth.json", "w+") as auth:
            auth.write(json.dumps({
                "token": token,
                "uuid": uuid
            }))

    # TODO: Refactor login attemptors to have the same success sequence to remove redundancy

    def attempt_login_ms():
        set_processing_sheet(True, "Authenticating with Microsoft...")
        username = controls["mc_username"].value
        ms_email = controls["ms_email"].value
        ms_password = controls["ms_password"].value

        result = requests.get(RECAPE_URL + "/authenticate/ms_login", headers={"email": ms_email, "password": ms_password, "username": username, "source": "ReCape Client " + VERSION})

        result = result.json()

        set_processing_sheet(False)
        if result["status"] == "failure":
            confirm_action(result["error"])
        elif result["status"] == "success":
            confirm_action("Successfully authenticated your account! Welcome to ReCape. The client will now attempt to restart.")

            API.save_credentials(result["token"], result["uuid"])

            page.window_destroy()

            os.execl(sys.executable, sys.executable, *sys.argv)
    
    def attempt_login_code():
        set_processing_sheet(True, "Authenticating with code...")
        username = controls["mc_username"].value
        code = controls["server_code"].value

        result = requests.get(RECAPE_URL + "/authenticate/server_code", headers={"code": code, "username": username, "source": "ReCape Client " + VERSION}, verify=not DEBUG)

        result = result.json()

        set_processing_sheet(False)

        if result["status"] == "failure":
            confirm_action(result["error"])
        elif result["status"] == "success":
            confirm_action("Successfully authenticated your account! Welcome to ReCape. The client will now attempt to restart.")

            API.save_credentials(result["token"], result["uuid"])

            page.window_destroy()

            os.execl(sys.executable, sys.executable, *sys.argv)

    def set_cape(friendly, cape):
        set_processing_sheet(True, "Sending cape to servers...")
        credentials = API.read_credentials()

        files = {}
        cape_type = "custom"
        if not cape.endswith(".png"):
            cape_type = cape
        else:
            files = {"file": open(PATH_PREFIX + "assets/capes/" + cape, "rb")}
        
        result = requests.post(RECAPE_URL + "/account/set_cape", headers={"uuid": credentials["uuid"], "token": credentials["token"], "cape_type": cape_type}, files=files, verify=not DEBUG)

        result = result.json()

        set_processing_sheet(False)

        if result["status"] == "success":
            confirm_action("Successfully set cape to: " + friendly)
        elif result["status"] == "failure":
            confirm_action(result["error"])
        else:
            confirm_action("*shrugs*") # ignorance is bliss
    
    def get_config():
        credentials = API.read_credentials()

        if credentials == None:
            return False

        try:
            result = requests.get(RECAPE_URL + "/account/get_config", headers={"uuid": credentials["uuid"], "token": credentials["token"]}, verify=not DEBUG)
        except requests.exceptions.ConnectionError:
            return False

        print(result.text)

        result = result.json()

        if not "status" in result.keys():
            return result
        if result["status"] == "failure":
            return False
        else:
            return result
    
    def get_cosmetic_list():
        credentials = API.read_credentials()

        if credentials == None:
            return False
        
        try:
            result = requests.get(RECAPE_URL + "/account/get_cosmetic_list", headers={"uuid": credentials["uuid"], "token": credentials["token"]}, verify=not DEBUG)
        except requests.exceptions.ConnectionError:
            return {}

        result = result.json()

        print(result)

        if result["status"] == 'failure':
            return {}

        return result["models"]
    
    def set_models():
        set_processing_sheet(True, "Sending model configuration to servers...")

        credentials = API.read_credentials()
        data = {}
        for check in model_checks.keys():
            data[check] = model_checks[check].value
        
        print(data)
        
        result = requests.post(RECAPE_URL + "/account/set_config", headers={"uuid": credentials["uuid"], "token": credentials["token"], "config": json.dumps(data)}, verify=not DEBUG)
        set_processing_sheet(False)
        confirm_action("Successfully updated models")

class CapeButton(ft.UserControl):

    def __init__(self, image, text, cape_value=None):
        self.image = image
        self.text = text
        self.cape = cape_value
        super().__init__()

    def build(self):
        return ft.Container(
            ft.Column([
            ft.Image(self.image, border_radius=10, aspect_ratio=1),
            ft.Text(self.text)
        ], 
        alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        on_click=lambda ev: API.set_cape(self.text, self.cape)
        )

class ModelButton(CapeButton):

    def __init__(self, text, model_value=None, activated=False):
        self.text = text
        self.model = model_value
        self.activated = activated
        super().__init__(None, text, model_value)

    def build(self):
        return ft.Container(
            ft.Column([
            ft.Text(self.text[0], size=35),
            ft.Text(self.text),
            add_model_check(self.model, ft.Checkbox(label="Enable?", value=self.activated))
        ], 
        alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        )
    
def confirm_action(text):
    page.snack_bar = ft.SnackBar(ft.Text(text))
    page.snack_bar.open = True
    page.update()

def set_processing_sheet(open=True, text=None):
    processing_sheet.open = open
    if text:
        controls["loading_text"].value = text
    page.update()

def install():
    result = installer.install()

    if result == "success":
        confirm_action("Successfuly installed ReCape! You may need to restart your computer.")
    elif result == "denied":
        confirm_action("ReCape could not be installed because we could not get permission to edit the hosts file (the system file that we need to change to redirect OptiFine servers to ours). Please run the ReCape installer again with administrator/root access.")
    else:
        confirm_action("*shrugs*")

def uninstall():
    result = installer.uninstall()

    if result == "success":
        confirm_action("Successfuly uninstalled ReCape. You may need to restart your computer.")
    elif result == "denied":
        confirm_action("ReCape could not be uninstalled because we could not get permission to edit the hosts file (the system file that we need to change to redirect OptiFine servers to ours). Please run the ReCape installer again with administrator/root access.")
    else:
        confirm_action("*shrugs*")

processing_sheet = ft.BottomSheet(
        ft.Container(
            ft.Column(
                [
                    ft.ProgressRing(),
                    add_control("loading_text", ft.Text("Loading...", size=30))
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER

            ),
            padding=10,
        ),
        open=False,
        on_dismiss= lambda ev: set_processing_sheet(True, "Be patient!")
    )

tabs = [
    ft.Tab(
    text="Welcome",
    icon=ft.icons.WAVING_HAND_ROUNDED,
    content=ft.Container(
    ft.Column(
                    [
    ft.Row([ft.Icon(name=ft.icons.DISCORD), ft.ElevatedButton(text="Join the Discord", on_click=lambda ev: webbrowser.open("https://discord.gg/HNUhexqusj"))]),
    ft.Row([ft.Icon(name=ft.icons.REDDIT), ft.ElevatedButton(text="Join the Subreddit", on_click=lambda ev: webbrowser.open("https://www.reddit.com/r/ReCape/"))]),
    ft.Row([ft.Icon(name=ft.icons.SOURCE), ft.ElevatedButton(text="View the Source", on_click=lambda ev: webbrowser.open("https://github.com/ReCape"))]),
    
    ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER
    ),
    alignment=ft.alignment.center,
    image_src="background.png",
    image_fit=ft.ImageFit.COVER,
    expand=True,
    margin=0
    ),
    ),

    ft.Tab(
    text="Account",
    icon=ft.icons.PERSON,
    content=ft.Container(
    ft.Column(
                    [
    
    ft.Text("Account", size=30), 
    ft.Text("You're not logged in yet! Login with Microsoft to provide your Microsoft email and password to verify. If you don't feel comfortable doing that, use Server verification to connect your Minecraft account to a server and receive a code.", text_align=ft.TextAlign.JUSTIFY), 
                     
    add_control("mc_username", ft.TextField(label="Minecraft Username")),
                     
    ft.Container(ft.Column([
    
        add_control("ms_email", ft.TextField(label="Microsoft Email")),
        add_control("ms_password", ft.TextField(label="Microsoft Password", password=True, can_reveal_password=True)),
        ft.ElevatedButton("Login with Microsoft", on_click=lambda ev: API.attempt_login_ms()),

    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER), border=ft.border.all(1, "black"), border_radius=4, padding=4, bgcolor=ft.colors.BLACK26
    ), 

    ft.Text("OR"),

    ft.Container(
    ft.Column([
    
        ft.Text("In Minecraft, connect to verify.recape.boyne.dev to receive your code"),
        
        add_control("server_code", ft.TextField(label="Code")),
        ft.ElevatedButton("Verify with Server", on_click=lambda ev: API.attempt_login_code()),

    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER), border=ft.border.all(1, "black"), border_radius=4, padding=4, bgcolor=ft.colors.BLACK26)
                    
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER
    ),
    alignment=ft.alignment.center,
    )
    ),

    ft.Tab(
    text="Install",
    icon=ft.icons.DOWNLOAD,
    content=ft.Container(
    ft.Column(
                    [
    ft.Text("Installing is really, really easy. It's kind of ridiculous."),
    ft.Row([ft.Icon(name=ft.icons.CHECK), ft.ElevatedButton(text="Install", on_click=lambda ev: install())], alignment=ft.MainAxisAlignment.CENTER),
    ft.Row([ft.Icon(name=ft.icons.CLOSE_ROUNDED), ft.ElevatedButton(text="Uninstall", on_click=lambda ev: uninstall())], alignment=ft.MainAxisAlignment.CENTER),
    ft.Text(installer.get_installer_text()),
    
    ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True
    ),
    alignment=ft.alignment.center,
    expand=True,
    margin=0
    ),
    ),

    ft.Tab(
    text="Cape",
    icon=ft.icons.RECTANGLE_ROUNDED,
    content=ft.Container(
    ft.Column(
                    [
                    ft.Row([
    ft.Text("Cape", size=30),
    ft.ElevatedButton("Import Cape", icon=ft.icons.ADD, on_click=lambda e: cape_picker.pick_files(allow_multiple=False))
                     ],
                     alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                     vertical_alignment=ft.CrossAxisAlignment.CENTER), 
                     add_control("cape_grid", ft.GridView(expand=1, runs_count=5,max_extent=150, spacing=40, run_spacing=5))], horizontal_alignment=ft.CrossAxisAlignment.CENTER
    ),
    alignment=ft.alignment.center,
    )
    ),

    ft.Tab(
    text="Model",
    icon=ft.icons.PERSON_ADD_ROUNDED,
    content=ft.Container(
    ft.Column(
                    [
    ft.Row([
    ft.Text("Model", size=30),
    ft.ElevatedButton("Apply Changes", icon=ft.icons.UPLOAD, on_click=lambda e: API.set_models()),
    ft.ElevatedButton("Import Model", icon=ft.icons.ADD, on_click=lambda e: model_picker.pick_files(allow_multiple=False, allowed_extensions=["cfg"], dialog_title="Choose a model .cfg file"))
                     ],
                     alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                     vertical_alignment=ft.CrossAxisAlignment.CENTER), 
                     add_control("model_grid", ft.GridView(expand=1, runs_count=5,max_extent=150, spacing=40, run_spacing=5))], horizontal_alignment=ft.CrossAxisAlignment.CENTER
    ),
    alignment=ft.alignment.center,
    )
    ),

    ft.Tab(
    text="Help",
    icon=ft.icons.QUESTION_MARK,
    content=ft.Container(
    ft.Column(
        [
    ft.Text("Help me!", size=30, text_align=ft.TextAlign.JUSTIFY),
    HELP], 
    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    scroll=ft.ScrollMode.ADAPTIVE
    ),
    alignment=ft.alignment.center,
    )
    ),

    ft.Tab(
    text="About",
    icon=ft.icons.INFO_OUTLINE,
    content=ft.Container(
    ft.Column(
                    [ft.Text(ABOUT, size=20, text_align=ft.TextAlign.JUSTIFY)], 
                    alignment=ft.MainAxisAlignment.CENTER, 
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    scroll=ft.ScrollMode.ALWAYS
    ),
    alignment=ft.alignment.center,
    )
    )
]

def main(target_page: ft.Page):
    global page
    page = target_page
    page.title = "ReCape"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.scroll = None

    page.overlay.append(processing_sheet)
    page.overlay.append(cape_picker)
    page.overlay.append(model_picker)
    page.overlay.append(texture_picker)

    load_capes()
    load_models()

    #controls["model_grid"].controls.append(ModelButton("no-cape.png", "No Model"))

    load_logged_in_page()

    page.add(ft.Tabs(tabs=tabs, expand=1, animation_duration=200))

ft.app(target=main, assets_dir="assets")