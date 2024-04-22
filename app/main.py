import datetime
import subprocess
import sys
import threading
import time
import webbrowser

import docker
from PyQt5.QtCore import QDate, QDateTime, Qt, QTime, QTimer
from PyQt5.QtGui import QColor, QFont, QIcon
from PyQt5.QtWidgets import (QAction, QApplication, QMainWindow, QMenu,
                             QSystemTrayIcon, QTextEdit)

from media_dock_logger import Logger

client = docker.from_env(timeout=120)

containers_running = False
containers_running_lock = threading.Lock()


def threaded_function(func):
    """ Decorator to run a function in a new thread and return the thread. """
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=func, args=args, kwargs=kwargs)
        thread.daemon = True  # Daemon threads exit when the main program does
        thread.start()
        return thread
    return wrapper


@threaded_function
def check_installations():
    """Check if Docker and Docker Compose are installed and handle errors appropriately."""
    try:
        subprocess.run(["docker", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        Logger.SUCCESS("Docker is installed.")
    except subprocess.CalledProcessError:
        Logger.ERROR("Docker is not installed. Please install Docker before running this script.")
        return False  # Return False to indicate failure

    try:
        subprocess.run(["docker-compose", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        Logger.SUCCESS("Docker Compose is installed.")
    except subprocess.CalledProcessError:
        Logger.ERROR("Docker Compose is not installed. Please install Docker Compose before running this script.")
        return False

    return True  # Return True to indicate success

@threaded_function
def are_containers_running():
    global containers_running
    required_containers = ['jellyseerr', 'openvpn-client', 'sonarr', 'radarr', 'prowlarr', 'qbittorrent']
    try:
        running_containers = {container.name: container for container in client.containers.list()}
        all_running = all(name in running_containers for name in required_containers)
        with containers_running_lock:
            containers_running = all_running
        if not all_running:
            missing_containers = [name for name in required_containers if name not in running_containers]
            Logger.WARNING("The following required containers are not running: " + ', '.join(missing_containers))
        return all_running
    except Exception as e:
        Logger.ERROR(f"Failed to check if containers are running due to an error: {str(e)}")
        with containers_running_lock:
            containers_running = False
        return False

@threaded_function
def build_and_start_containers():
    """ Build and start containers using Docker Compose, ensuring images are built if necessary. """
    Logger.INFO("Attempting to setup containers using Docker Compose with build option...")
    try:
        subprocess.run(["docker-compose", "-f", "../docker-compose.yml", "up", "-d", "--build"], check=True)
        Logger.SUCCESS("Containers have been built and started successfully.")
    except subprocess.CalledProcessError as e:
        Logger.ERROR(f"Failed to build/start containers using Docker Compose: {e}")
        return False

    return True

@threaded_function
def update_container(container):
    if container.name == "openvpn-client":
        Logger.INFO(f"Skipping update check for {container.name} as it is manually managed.")
        return

    Logger.INFO(f"Attempting to check updates for {container.name}")
    try:
        current_image = container.image.tags[0]
        repository, tag = current_image.split(":")
        try:
            new_image = client.images.pull(f"{repository}:{tag}")
            new_image_id = new_image.id
        except Exception as pull_error:
            Logger.WARNING(f"Failed to pull image using Docker API: {str(pull_error)}. Trying with subprocess...")
            result = subprocess.run(["docker", "pull", f"{repository}:{tag}"], capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception(f"Failed to pull image using subprocess: {result.stderr}")
            new_image_id = client.images.get(f"{repository}:{tag}").id
        
        if new_image_id != container.image.id:
            Logger.INFO(f"Updating {container.name} to new image {new_image_id}")
            container.stop()
            container.remove()
            
            ports = {port: host_port for port, host_port in container.attrs['HostConfig']['PortBindings'].items()}
            volumes = {mount['Source']: {'bind': mount['Destination'], 'mode': mount['Mode']} for mount in container.attrs['Mounts']}
            
            client.containers.run(f"{repository}:{tag}", name=container.name, detach=True, ports=ports, volumes=volumes)
            Logger.SUCCESS(f"{container.name} updated and restarted.")
        else:
            Logger.INFO(f"No update available for {container.name}")
    except Exception as e:
        Logger.ERROR(f"Failed to update {container.name}: {str(e)}")

@threaded_function
def update_all_containers():
    Logger.INFO("Update process is starting.")
    
    are_containers_running_thread = are_containers_running()
    are_containers_running_thread.join()

    if not containers_running:
        Logger.WARNING("Containers are not running. Please run 'Setup' from the system tray icon.")
        return True

    required_containers = ['jellyseerr', 'openvpn-client', 'sonarr', 'radarr', 'prowlarr', 'qbittorrent']
    all_containers = client.containers.list()
    containers_to_update = [container for container in all_containers if container.name in required_containers]
    
    update_failures = []
    for container in containers_to_update:
        if not update_container(container):
            update_failures.append(container.name)

    if update_failures:
        Logger.ERROR("Failed to update some containers: " + ", ".join(update_failures))
    
def calculate_msecs_until_next_one_am():
    """ Calculate how many milliseconds until the next occurrence of 01:00 AM. """
    now = QDateTime.currentDateTime()
    next_one_am = QDateTime(QDate.currentDate(), QTime(1, 0))
    if now > next_one_am:
        next_one_am = next_one_am.addDays(1)
    msecs_to_next_one_am = now.msecsTo(next_one_am)
    return msecs_to_next_one_am

def schedule_daily_update():
    """ Schedule the update_all_containers function to run daily at 01:00 AM. """
    msecs = calculate_msecs_until_next_one_am()
    QTimer.singleShot(msecs, perform_daily_update)

def perform_daily_update():
    """ Perform the update and reschedule the next update. """
    update_all_containers()
    schedule_daily_update() 

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.tray_icon = QSystemTrayIcon(QIcon("MediaDock.ico"), self) 
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Media Dock")
        self.setWindowFlags(Qt.Window)
        self.setWindowIcon(QIcon("MediaDock.ico"))
        self.resize(900, 600) 

        # QTextEdit stilini ayarla
        self.log_panel = QTextEdit(self)
        self.log_panel.setReadOnly(True) 
        self.log_panel.setStyleSheet("""
            background-color: #333;
            color: #fff;
            font-family: 'Consolas', 'Courier New', monospace;
            border: 1px solid #333;
        """)
        self.log_panel.setFont(QFont('Consolas', 10)) 
        self.setCentralWidget(self.log_panel)
        Logger.set_log_widget(self.log_panel)
        
    def closeEvent(self, event):
        self.hide()
        event.ignore() 
        
class TrayApplication(QApplication):
    def __init__(self, *args, **kwargs):
        super(TrayApplication, self).__init__(*args, **kwargs)
        self.window = MainWindow()
        self.setSystemTrayIcon()
        
        
    def setSystemTrayIcon(self):
        # Icon setup here
        self.window.tray_icon.setIcon(QIcon("MediaDock.ico"))
        self.window.tray_icon.setToolTip("Media Dock Running")
        self.window.tray_icon.setVisible(True)  

        # Tray Menu
        tray_menu = QMenu()
        open_action = QAction("Show", self)
        update_action = QAction("Update Now", self)
        setup_action = QAction("Setup", self)
        about_action = QAction("About", self)
        quit_action = QAction("Exit", self)

        open_action.triggered.connect(self.window.showNormal)
        update_action.triggered.connect(self.update_now)
        setup_action.triggered.connect(self.setup_containers)
        about_action.triggered.connect(self.show_about)
        quit_action.triggered.connect(self.quitApplication)

        tray_menu.addAction(open_action)
        tray_menu.addAction(update_action)
        tray_menu.addAction(setup_action)
        tray_menu.addAction(about_action)
        tray_menu.addSeparator()
        tray_menu.addAction(quit_action)

        self.window.tray_icon.setContextMenu(tray_menu)
        self.window.tray_icon.show()
        
        self.window.tray_icon.activated.connect(self.on_tray_icon_activated)

    def update_now(self):
        """Manually triggers the update process and ensures the application does not exit unexpectedly."""
        self.window.showNormal()
        Logger.INFO("Manual update triggered.")

        # update_all_containers işlevini başlat ve sonunu bekle
        update_thread = update_all_containers()
        update_thread.join()  # Thread'in bitmesini bekle

        # Thread tamamlandığında, başarı veya başarısızlık durumunu kontrol et ve logla
        if not containers_running:
            Logger.ERROR("Update failed. Please check the logs for more details.")
        else:
            # Logger.SUCCESS("All containers updated successfully.")
            pass



    def setup_containers(self):
        Logger.INFO("Setting up containers...")
        build_and_start_containers_thread = build_and_start_containers()
        build_and_start_containers_thread.join()
        Logger.SUCCESS("Containers setup completed.")

    def show_about(self):
        github_url = "https://github.com/gkhntpbs/MediaDock"
        webbrowser.open(github_url)

    def on_tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.window.showNormal()

    def quitApplication(self):
        # Quit the application cleanly
        self.window.tray_icon.hide()
        self.quit() 
        
if __name__ == "__main__":
    app = TrayApplication(sys.argv)
    app.window.show()

    install_thread = check_installations()
    install_thread.join()

    container_thread = are_containers_running()
    container_thread.join()

    with containers_running_lock:
        if not containers_running:
            build_thread = build_and_start_containers()
            # build_thread.join()
        else:
            Logger.INFO("All required containers are already running.")

    schedule_daily_update()
    Logger.INFO("Update scheduler is set up. Update Check will occur at 01:00 AM.")
    sys.exit(app.exec_())




