
import dns.resolver
import platform

class Installer:
    def __init__(self, RECAPE_URL, DEBUG):

        current_os = platform.system()

        print(current_os)

        self.LINE_IDENTIFIER = "ADDED BY RECAPE"

        try:
            self.hosts_file_dir = {
                "Windows": "C:\Windows\System32\drivers\etc\hosts",
                "Linux": "/etc/hosts",
                "Darwin": "/private/etc/hosts"
            }[current_os]
        except KeyError:
            self.hosts_file_dir = "/etc/hosts"

        self.OPTIFINE_URL = "s.optifine.net"
        self.RECAPE_URL = RECAPE_URL.replace("https://", "")

        if DEBUG:
            self.RECAPE_IP = "127.0.0.1"
        else:
            self.RECAPE_IP = dns.resolver.resolve(self.RECAPE_URL)[0].to_text()

    def install(self):
        self.uninstall()
        try:

            with open(self.hosts_file_dir, "r") as hosts:
                content = hosts.readlines()
            with open(self.hosts_file_dir, "w") as hosts:
                content.append("\n" + self.RECAPE_IP + " " + self.OPTIFINE_URL + " #" + self.LINE_IDENTIFIER)
                hosts.write("".join(content))

        except PermissionError as e:

            print(e)

            print("Access Denied")
            return "denied"

        return "success"

    def uninstall(self):
        try:
            with open(self.hosts_file_dir, "r") as hosts:
                content = hosts.readlines()
                for i in range(0, len(content)):
                    if self.LINE_IDENTIFIER in content[i]:
                        content.pop(i)
                        break
            with open(self.hosts_file_dir, "w") as hosts:
                hosts.write("".join(content))
        except PermissionError:
            print("Access Denied")
            return "denied"

        return "success"

    def get_installer_text(self):
        return "You can also install ReCape yourself by manually inputting text into your hosts file. On your system, this file should be located at \"" + self.hosts_file_dir + "\". On a new line, put in this text:\n" + self.RECAPE_IP + " " + self.OPTIFINE_URL + " #" + self.LINE_IDENTIFIER + "\nSimilarly, you can uninstall ReCape by deleting that line in the hosts file later."