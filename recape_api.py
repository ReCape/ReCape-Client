import os
import json
import requests
import sys
import shutil

DEBUG = os.path.exists(".debug")

VERSION = "1.0"

RECAPE_URL = "https://localhost" if False else "https://recape-server.boyne.dev" #TODO: Change back to debug

# TODO: Implement
def restart():
    #page.window_destroy()

    os.execl(sys.executable, sys.executable, *sys.argv)

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

    def attempt_login_ms(username, ms_email, ms_password):
        result = requests.get(RECAPE_URL + "/authenticate/ms_login", headers={"email": ms_email, "password": ms_password, "username": username, "source": "ReCape Client " + VERSION})

        result = result.json()

        if result["status"] == "failure":
            return result["error"]
        elif result["status"] == "success":

            API.save_credentials(result["token"], result["uuid"])

            return ["Successfully authenticated your account! Welcome to ReCape.", True]
    
    def attempt_login_code(username, code):

        result = requests.get(RECAPE_URL + "/authenticate/server_code", headers={"code": code, "username": username, "source": "ReCape Client " + VERSION}, verify=not DEBUG)

        try:
            result = result.json()
        except requests.exceptions.JSONDecodeError:
            return result.text


        if result["status"] == "failure":
            return result["error"]
        elif result["status"] == "success":

            API.save_credentials(result["token"], result["uuid"])

            return ["Successfully authenticated your account! Welcome to ReCape.", True]
    
    def delete_credentials():
        folder = os.path.expanduser("~")
        folder += "/.recape"

        try:
            shutil.rmtree(folder)
            return ["Login credentials deleted!", True]
        except FileNotFoundError:
            return "There were no credentials to delete."
    
    def verify_credentials(token, uuid, username):
        try:
            result = requests.get(RECAPE_URL + "/authenticate/check_token", headers={"token": token, "uuid": uuid, "username": username}, verify=not DEBUG)
        except requests.exceptions.ConnectionError:
            return None

        result = result.json()

        return result["result"] == "valid"

    def set_cape(friendly, cape):
        credentials = API.read_credentials()

        files = {}
        cape_type = "custom"
        if not cape.endswith(".png"):
            cape_type = cape
        else:
            files = {"file": open(cape, "rb")}
        
        result = requests.post(RECAPE_URL + "/account/set_cape", headers={"uuid": credentials["uuid"], "token": credentials["token"], "cape_type": cape_type}, files=files, verify=not DEBUG)

        result = result.json()

        if result["status"] == "success":
            return "Successfully set cape to: " + friendly
        elif result["status"] == "failure":
            return result["error"]
        else:
            return "*shrugs*"
    
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
    
    def set_models(models):

        credentials = API.read_credentials()
        
        result = requests.post(RECAPE_URL + "/account/set_config", headers={"uuid": credentials["uuid"], "token": credentials["token"], "config": json.dumps(models)}, verify=not DEBUG)
        
        result = result.json()

        if result["status"] == "success":
                return "Successfully changed your models!"
        elif result["status"] == "failure":
            return result["error"]
        else:
            return "*shrugs*"
    
    def upload_model(model_path, texture_path):
        credentials = API.read_credentials()

        files = {}

        files = {"model": open(model_path, "rb"), "texture": open(texture_path, "rb")}  

        try: 
        
            result = requests.post(RECAPE_URL + "/account/upload_cosmetic", headers={"uuid": credentials["uuid"], "token": credentials["token"]}, files=files, verify=not DEBUG)

            result = result.json()

            if result["status"] == "success":
                return "Successfully uploaded the model files!"
            elif result["status"] == "failure":
                return result["error"]
            else:
                return "*shrugs*" # ignorance is bliss
        except Exception as e:
            return "An error occurred, and your model could not be uploaded. Check the Discord for downtime information. The error is: " + str(e)