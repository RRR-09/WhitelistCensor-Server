```
Debian 11
```

# Init + Setup SFTP access

1. `sudo apt update && sudo apt install && sudo apt autoremove && sudo reboot`
1. `sudo addgroup censor_service`
1. `sudo adduser censor`
1. `sudo usermod -G censor_service,sudo censor`
   > Can log out of root and execute further commands from `censor` user
1. `sudo adduser censor_data`
1. `sudo addgroup jailed_sftp_users`
1. `sudo usermod -G censor_service,jailed_sftp_users censor_data`
1. `sudo mkdir -p /jail/censor_data/home`
1. `sudo ln -s /jail/censor_data/home /home/censor/censor_data_dir`
1. `sudo chown root /jail/censor_data`
1. `sudo chmod 755 /jail/censor_data`
1. `sudo chown censor_data:censor_service /jail/censor_data/home`
1. `sudo chmod 770 /jail/censor_data/home`
1. `sudo chmod g+s /jail/censor_data/home`
   > SetGID permission flag, make any new/changed files accessible by anyone in the group regardless of owner
1. `sudo apt install acl`
1. `sudo setfacl -d -m o::- /jail/censor_data/home`
1. `sudo setfacl -d -m g::rwx /jail/censor_data/home`
   > Sets new subdirectories and their contents to also be group-RW
1. `sudo nano /etc/ssh/sshd_config`

   ```
   # Subsystem      sftp    /usr/lib/openssh/sftp-server
   Subsystem       sftp    internal-sftp

   Match Group jailed_sftp_users
     X11Forwarding no
     AllowTcpForwarding no
     ChrootDirectory /jail/%u
     ForceCommand internal-sftp
   ```

1. `sudo systemctl restart sshd`
1. `sudo usermod -d home/ censor_data`
   > After this, ensure:
   >
   > - Can SSH in as `censor`
   > - Can't SSH in as `censor_data`
   > - Can SFTP as `censor`
   >   - Defaults to `/home/censor`
   >   - Can R/W most places including `/jail/censor_data/home`
   >   - Can R/W files/folders created by `censor_data`
   > - Can SFTP as `censor_data`
   >   - Defaults to `/jail/censor_data/`
   >   - Can R/W in the `home` folder and nowhere else
   >   - Can't see any folders above or adjacent to `/jail/censor_data/`
   >   - Can R/W files/folders created by `censor`
   >
   > NOTE: Be aware, over SFTP creating a file and folder with the same name (`./test` and `./test/`) will not work, will silently fail, and look like a permission issue.

# Cloning & Installing PyEnv/Poetry/UFW

Assuming working directory of `/home/censor/`.

1. `git clone (this repo's URL)`
1. `mv (the cloned folder) whitelist_server`
   > Optional, will refer to this folder as `whitelist_server` for rest of instructions
1. `sudo apt install build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libreadline-dev libffi-dev libsqlite3-dev wget libbz2-dev liblzma-dev`
   > Core dependencies for Python
1. - `curl https://pyenv.run | bash`
   - `nano ~/.profile`
   - Add
     ```
     export PATH="$HOME/.pyenv/bin:$PATH"
     eval "$(pyenv init --path)"
     eval "$(pyenv virtualenv-init -)"
     ```
   - Re-login
   - `pyenv --version`

   - `pyenv install 3.10.`
   - `pyenv local 3.10.`
   - `python --version`
     > Optional, Python 3.10 <= recommended

1. - `curl -sSL https://install.python-poetry.org | python -`
   - `nano ~/.profile`
   - Add

   ```
   export PATH="$HOME/.local/bin:$PATH"
   ```

   - Re-login
     > Installs Poetry using the PyEnv version of python. Substitute "`| python -`" if needed.

1. - `sudo apt install ufw`
   - `sudo ufw allow ssh`
   - `sudo ufw allow 8087`
   - `sudo ufw enable`

# Setup & Launch

1. `cd whitelist_server`
1. `poetry install`
1. `cd censor_server`
1. Create/populate `config.json` and `.env` based on the adjacent example files in `censor_server` directory

   - Change `ws_server_ip` to something like `0.0.0.0`
   - Set `data_path` config option to `["/","jail","censor_data","home","whitelist_data"]`
   - Create folder in `/jail/censor_data/home/`, i.e. `whitelist_data`
   - Copy/upload any datasets to that folder

1. `poetry run python watchdog.py`
