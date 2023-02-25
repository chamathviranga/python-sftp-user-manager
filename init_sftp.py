#Info
    # A project : For Fun 
    # Created by : Chamath Viranga
    # Licence : Feel free to use as you wish
    # Referance : https://www.techrepublic.com/article/how-to-set-up-an-sftp-server-on-linux/
    # Emoji : https://unicode.org/emoji/charts/full-emoji-list.html

# Flow
    # get user input
    # Create new user for sftp
    # Create sftp user group if not exist
    # Assign sftp user to sftp group
    # Add new configurations to sshd_config
    # Print sftp username and password with help commands

# More Commands :
    # Remove user : userdel -r USER_NAME
    # Remove group : group del GROUP_NAME
    # Custom sshd config path : /etc/ssh/sshd_config.d/FILE_NAME.conf (sshd_config will load files automatically in this path)

import getpass
import grp
import subprocess
import sys
import argparse


class SFTP:

    username = None
    password = None
    group = "sftp"
    sudo_pass = None
    sftp_directory = None

    def __init__(self):
        
        # Create the argument parser
        parser = argparse.ArgumentParser(description='Create or delete SFTP user accounts')

        # Define the command-line arguments
        parser.add_argument('--init', action='store_true', help='Create new SFTP account')
        parser.add_argument('--delete', action='store_true', help='Delete existing SFTP user')

        # Parse the arguments
        args = parser.parse_args()

        if args.init:
            self.run()
        elif args.delete:
            self.delete_user()
        else:
            print("\r\nInvalid argument provided. Please provid \r\n\r\n--init (Create SFTP user) \r\n--delete (Delete SFTP user)\r\n")


        

    def run(self):
        # Get user inputs
        self.get_user_inputs()
        # Create new SFTP group
        #self.new_user_group(False)
        # Create new user
        self.new_user(False)
        # Assign user to SFTP group
        self.assign_user_to_ftp_group()
        # Create data directory
        self.make_sftp_directory()
        # Set config
        self.set_config()
        # Finalize user creation
        self.complete_user_creation()


    def get_user_inputs(self):
        print(f"\r\nGenerating new SFTP user.\r\n (Default SFTP user group is `sftp`) \r\n\r\n")
        self.username = input("Enter username for the user \U0001F464 : ")
        self. password = input("Enter password for the user \U0001F511 : ")
        #self.group = input(f"Enter group for the SFTP user ({self.username}) : ")
        self.sudo_pass = getpass.getpass(prompt="Enter password for sudo \U0001F9B8 : ")

    def new_user_group(self, new_group):

        if new_group:
            self.group = input(f"Enter group for the SFTP user ({self.username}) : ")

        # Check group exist
        try:

            grp.getgrnam(self.group)
            print(f"\r\n{self.group} group exists, Do you want to create another group (y/n) ?\r\n")

            while True:
                choose = input("Enter option : ")
                if choose.isalpha() and (choose == "y" or choose == "n"):
                    if choose == "y":
                        self.group = None
                        self.new_user_group(True)
                    elif choose == "n":
                        pass
                    break

        except KeyError:
            subprocess.run(["sudo", "-S", "groupadd", self.group], input=bytes(self.sudo_pass + "\n", "utf-8"), stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            print(f"\r\nNew group created ({self.group}) successfully.")

    def new_user(self, new_user):
        if new_user:
            self.username = input("Enter new username for the user \U0001F464 : ")
            self.password = input(f"Enter new password for the user({self.username}) \U0001F511 : ")
        try:
            # Check if user exists
            subprocess.run(["sudo", "-S", "id", self.username], input=bytes(self.sudo_pass + "\n", "utf-8"), stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            print("\r\nUser already exists, Do you want to create new user(y) , exit(e) or continue(c) ?\r\n")

            while True:
                choose = input("Enter option : ")
                if choose.isalpha() and (choose == "y" or choose == "e" or choose == "c"):
                    if choose == "y":
                        self.username = None
                        self.new_user(True)
                    elif choose == "e":
                        sys.exit()
                    elif choose == "c":
                        pass

                    break

        except subprocess.CalledProcessError:
            # Create user if it doesn't exist
            command = f"useradd -p $(openssl passwd -1 {self.password}) {self.username}"
            #subprocess.run(["sudo", "-S", "useradd", self.username])
            # subprocess.run(["sudo", "-S", "useradd", "-g", f"{self.group}", "-d", "/upload", "-s", "/sbin/nologin", f"{self.username}"], input=bytes(self.sudo_pass + "\n", "utf-8"), check=True)
            try:
                subprocess.run(command, shell=True, check=True)
                print(f"\r\nNew user \U0001F60E '{self.username}' created with password \U0001F511 '{self.password}'\r\n")
            except subprocess.CalledProcessError as e:
                print(f"Error creating user: {e}")
            
    def assign_user_to_ftp_group(self):
        try:
            # Add user to group
            subprocess.run(["sudo", "-S", "usermod", "-a", "-G", self.group, self.username], input=bytes(self.sudo_pass + "\n", "utf-8"), check=True)
            print(f"User {self.username} added to group {self.group}")
        except subprocess.CalledProcessError as e:
            print(f"Error adding user {self.username} to group {self.group}: {e}")

    def set_config(self):
        try:
            with open(f"/etc/ssh/sshd_config.d/{self.username}_sshd.conf", 'a') as f:
                f.write(f"Match User {self.username}\n")
                f.write('\tChrootDirectory /data/%u\n')
                f.write('\tForceCommand internal-sftp\n')
                f.write('\tX11Forwarding no\n')
                f.write('\tAllowTcpForwarding no\n')

        except PermissionError:
            print("Permission denied. Try running the program with administrative privileges.")
        except Exception as e:
            print(f"Error while setting the SSH config: {e}")

    def make_sftp_directory(self):
        subprocess.run(["sudo", "-S", "mkdir", "-p", f"/data/{self.username}/upload"], input=bytes(self.sudo_pass + "\n", "utf-8"), check=True)
        subprocess.run(["sudo", "-S", "chmod", "701", "/data/"], input=bytes(self.sudo_pass + "\n", "utf-8"), check=True)
        subprocess.run(["sudo", "-S", "chown", "-R", f"root:{self.group}", f"/data/{self.username}"], check=True)
        subprocess.run(["sudo", "-S", "chown", "-R", f"{self.username}:{self.group}", f"/data/{self.username}/upload"], check=True)

    def complete_user_creation(self):
        print(f"\r\nRestarting SSHD Service")
        try:
            subprocess.run(["sudo", "-S", "systemctl", "restart", "sshd"], input=bytes(self.sudo_pass + "\n", "utf-8"), check=True)
            print(f"\r\n\u2705 Restarting completed")
        except Exception as e:
            print(f"Faild to restart sshd {e}")
            print(f"Restarting SSHD service again \r\n")
            subprocess.run(["sudo", "-S", "/etc/init.d/ssh", "restart"], input=bytes(self.sudo_pass + "\n", "utf-8"), check=True)

        
        print(f"\u2705 New SFTP user created successfully.\r\n")
        print(f"Username : {self.username}")
        print(f"Password : {self.password}")
        print(f"Connect to sftp : \U0001F525 >>:_ sftp {self.username}@_YOUR_SERVER_IP \U0001F525 \r\n\r\n")


    def __del__(self):
        pass        


    def delete_user(self):
        print(f"\r\nDelete SFTP user account \U0001F62A\U0001F494\r\n")

        username = input("Enter username \U0001F464 : ")
        sudo_pass = getpass.getpass(prompt="Enter password for sudo \U0001F9B8 : ")

        try:
            print("\u2705 Deleting user files")
            subprocess.run(["sudo", "-S", "deluser", "--remove-all-files", username], input=bytes(sudo_pass + "\n", "utf-8"), check=True)
            print("\r\n\u2705 Deleting sftp configuration file")
            subprocess.run(["sudo", "-S", "rm", f"/etc/ssh/sshd_config.d/{username}_sshd.conf"], input=bytes(sudo_pass + "\n", "utf-8"), check=True)
            print("\u2705 Deleting Restarting sshd service")
            subprocess.run(["sudo", "-S", "systemctl", "restart", "sshd"], input=bytes(sudo_pass + "\n", "utf-8"), check=True)
            print("\u2705 Deleting Deleting sftp direcory")
            subprocess.run(["sudo", "-S", "rm", "-rf", f"/data/{username}"], input=bytes(sudo_pass + "\n", "utf-8"), check=True)
            print("\r\n\u274C User deleted \u274C\r\n")
        except Exception as e:
            print(f"Faild to delete user ({username}) : {e}")
            print(f" -- May be you should run the script again ;) --")


if __name__ == "__main__":
    sftp = SFTP()
