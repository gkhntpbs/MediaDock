import re
import time

from PyQt5.QtWidgets import QTextEdit


class Logger:
    log_widget = None  # Log mesajlarını gösterecek widget
    log_to_file = True
    log_file_name = "mediadock.log"
    category = "[MediaDock]"
    
    @staticmethod
    def set_category(new_category):
        Logger.category = new_category

    @staticmethod
    def set_log_widget(widget: QTextEdit):
        Logger.log_widget = widget

    @staticmethod
    def log_message(level_color, level, message):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        # Yalnızca level etiketi renkli, diğer kısımlar gri olacak şekilde düzenleme
        log_message_console = (
            f"<span style='color:#fff;'>({timestamp}) {Logger.category}:</span> "
            f"<span style='color:{level_color};'>{level}</span> "
            f"<span style='color:#fff;'>{message}</span>"
        )
        if Logger.log_widget:
            Logger.log_widget.append(log_message_console)
        
        if Logger.log_to_file:
            # HTML etiketlerini ve renk kodlarını kaldır
            log_message_file = re.sub(r'<[^>]+>', '', log_message_console)
            with open(Logger.log_file_name, "a", encoding="utf-8") as log_file:
                log_file.write(log_message_file + "\n")

    @staticmethod
    def INFO(message):
        Logger.log_message("cyan", "[INFO]", message)

    @staticmethod
    def WARNING(message):
        Logger.log_message("yellow", "[WARNING]", message)

    @staticmethod
    def ERROR(message):
        Logger.log_message("red", "[ERROR]", message)

    @staticmethod
    def SUCCESS(message):
        Logger.log_message("green", "[SUCCESS]", message)
