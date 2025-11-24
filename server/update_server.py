
import datetime
import json
import logging
import os, os.path
import shutil
import socket
import subprocess
from subprocess import call
import sys
import time
import urllib2
import errno
import zipfile



SOFTWARE_URL_BASE="http://fathomdrone.com/firmwareupdate"
software_new_version = "-1"
SOFTWARE_INFO_FILE="FATHOM.json"
DOWNLOAD_DIR = "/tmp/fathom"
DOWNLOAD_MEDIA = DOWNLOAD_DIR+"/update.zip"

STAGING_DIR = DOWNLOAD_DIR + "/home/pi/DOWNLOADS/"
BACKUP_DIR = "/home/pi/BACKUP/"
INSTALL_LOCATION = "/home/pi/"

LOG_FILE="logs/fathom_update.log"
UPDATING_INDICATOR="/home/pi/SERVER/UPDATING.LOCK"

DEPENDENCY_DIR = "/home/pi/SERVER/lib"
PYTHON_REQS = DEPENDENCY_DIR + "/python_requirements.txt"

logger = None

# Get current version
def getCurrentVersion():
    v = "0.0"
    with open(SOFTWARE_INFO_FILE) as data_file:
        data = json.load(data_file)
        v = data["version"]
    return v

# Check internet access
def internet_on():
    global logger
    logger.info("Checking internet")
    i = False
    try:
        urllib2.urlopen('http://216.58.192.142', timeout=1)
        i = True
    except urllib2.URLError as err:
        i = False
        logger.info("Checking internet: urlerror")
        logger.info(err)
    except socket.timeout as e:
        i = False
        logger.info("Checking internet: timeout")

    logger.info("After checking internet")


    return i

# Indicate updating
def touch(path):
    with open(path, 'a'):
        os.utime(path, None)

# Indicate done updating
def removeUpdatingLock():
    os.remove(UPDATING_INDICATOR)

# Make download directory
def ensureDownloadDir():
    """
    Ensure that a named directory exists; if it does not, attempt to create it.
    """
    try:
        os.makedirs(DOWNLOAD_DIR)
    except OSError, e:
        if e.errno != errno.EEXIST:
            raise

# Make backup directory
def ensureBackupDir():
    """
    Ensure that a named directory exists; if it does not, attempt to create it.
    """
    try:
        os.makedirs(BACKUP_DIR)
    except OSError, e:
        if e.errno != errno.EEXIST:
            raise

    shutil.rmtree(BACKUP_DIR+"latest", ignore_errors=True)

# Make log directory
def ensureLogFile():
    if not os.path.exists(LOG_FILE):
        open(LOG_FILE, 'a').close()
        #os.makedirs(LOG_FILE)

# Check if new version is higher than current version
def isNewerVersion(new_version):
    if (float(new_version) > float(getCurrentVersion())):
        return True
    else:
        return False

# Download software update
def downloadSoftware():
    downloadSuccesful = True
    ensureDownloadDir()
    try:
        response = urllib2.urlopen(SOFTWARE_URL_BASE)
        zipcontent = response.read()
        with open(DOWNLOAD_MEDIA, 'w') as f:
            f.write(zipcontent)
    except urllib2.HTTPError, err:
        if err.code == 404:
            logger.error("Page not found!")
        elif err.code == 403:
            logger.error("Access denied!")
        else:
            logger.error("Something happened! Error code", err.code)
        downloadSuccesful = True
    except urllib2.URLError, err:
        logger.error("Some other error happened:", err.reason)
        downloadSuccesful = True

    return downloadSuccesful

# copy helper
def copyanything(src, dst):
    try:
        shutil.copytree(src, dst,ignore=shutil.ignore_patterns("RECORDINGS", "recordings"))
    except OSError as exc: # python >2.5
        if exc.errno == errno.ENOTDIR:
            shutil.copy(src, dst)
        else: raise

# Extract software
def extractSoftware():
    zip_ref = zipfile.ZipFile(DOWNLOAD_MEDIA, 'r')
    zip_ref.extractall(INSTALL_LOCATION)
    zip_ref.close()

# Install dependencies
def installDependencies():

    # check if there are python requirements to install
    if os.path.isfile(PYTHON_REQS):
        process = subprocess.Popen(["sudo pip install -r "+PYTHON_REQS])
        process.wait()

# Backup the old folder
def backupCurrentFirmware():
    global BACKUP_DIR, logger,INSTALL_LOCATION
    backupSuccessful = True

    logger.info("Ensuring backup directory...")
    ensureBackupDir()
    logger.info("Starting backup to " + BACKUP_DIR)

    # locate the firmware directory
    # TODO: get the size of the directory
    # TODO: check if enough room to make a backup
    # TODO: if not enough room, return error

    # copy all items from the directory to backup directory
    copyanything(INSTALL_LOCATION+"SERVER",BACKUP_DIR+"latest")
    # TODO: zip the new directory with timestamp or version
    # TODO: move zip to backups dir
    logger.info("Finished backup.")

    return backupSuccessful



# Copy software from staging to production
def moveFromStagingToProduction():
    # TODO: determine if we need this step
    return True

# Install Software
def installSoftware():
    extractSoftware()

    # update dependencies
    installDependencies()



# Check if we can access the software update
def isSoftwareUpdateReachable():
    global logger
    i = False
    try:
        urllib2.urlopen(SOFTWARE_URL_BASE, timeout=1)
        i = True
    except urllib2.URLError as err:
        i = False
        logger.info("Checking software reachable: "+err.reason)
    except socket.timeout as e:
        i = False
        logger.info("Checking software reachable: timeout")
        logger.info(e)

    return i

# turn off the ethernet
def switchEthernet(turnOn):
    global logger

    logger.info("Switching ethernet...")
    upOrDown = "up"
    if turnOn == False:
        upOrDown = "down"
    call("sudo ifconfig eth0 " + upOrDown, shell=True)
    logger.info("Ethernet switched.")



    return


def tryUpdate():
    global logger, SOFTWARE_URL_BASE,software_new_version,current_version
    # SETUP LOGGING
    logger = logging.getLogger('myapp')
    ensureLogFile()
    hdlr = logging.FileHandler(LOG_FILE)
    # formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] - %(message)s')
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr)
    logger.setLevel(logging.INFO)
    logger.info('Logging initiated...')
    ################

    # Log header with diagnostic info
    logger.info("\r\n#####################################\r\n"
                "ENVIRONMENT INFO \r\n"
                "#####################################")
    logger.info("TODO: add environment info")
    logger.info("\r\n#####################################\r\n"
                "#####################################")



    if len(sys.argv) > 2:
        SOFTWARE_URL_BASE = sys.argv[2]
        software_new_version = sys.argv[1]

    # Get current version
    version = getCurrentVersion()
    logger.info("Current version: " + version)
    print("VERSION " + version)
    logger.info("New version: "+software_new_version)
    print("NEW VERSION " + software_new_version)

    # check if should try an update
    if isNewerVersion(software_new_version) == False:
        logger.info("New version is not higher. Not trying update.")
        quit()
    else:
        # If not current,
        logger.info("New version is higher. Software needs to be updated...")

    # TODO: Check if battery is too low
    # TODO: Check if temperature is too hot


    # Check internet access
    isInternetOn = internet_on()

    if isInternetOn == False:
        # turn off ethernet
        switchEthernet(False)

        # wait 5 seconds
        time.sleep(20)

        # check again
        if internet_on():
            logger.info("Internet is on.")
        else:
            # internet is still off, turn on ethernet and exit
            switchEthernet(True)
            # exit
            quit()
    else:
       logger.info("Internet on: " + str(isInternetOn))

    # Check if we can access the software update
    if isSoftwareUpdateReachable():
        logger.info("Software update reachable: ")
    else:
        logger.info("Software cannot be reached.")
        # exit
        quit()




    # indicate that an update is in progress
    logger.info("Creating UPDATING.LOCK file...")
    touch(UPDATING_INDICATOR)

    # download new scripts to temporary directory
    logger.info("Downloading software...")
    downloadSoftware()
    logger.info("Software download finished at " + str(datetime.datetime.now()))

    # turn ethernet back on so we can communicate with the user
    switchEthernet(True)

    # Backup old install
    if backupCurrentFirmware():
        logger.info("Files successfully backed up")
    else:
        logger.info("Unable to create back up. Exiting")
        quit()

    # After download, start update
    logger.info("Starting install.")
    installSoftware()
    logger.info("Finished install at " + str(datetime.datetime.now()))

    # Indicate that update is complete
    logger.info("Removing UPDATING.LOCK file...")
    removeUpdatingLock()

    logger.info("Update finished at " + str(datetime.datetime.now()))
    logger.info("Exiting now.")

    # finally, reboot
    call("sudo reboot", shell=True)

    return 2
    # Exit


if __name__ == '__main__':
    # test1.py executed as script
    # do something
    tryUpdate()