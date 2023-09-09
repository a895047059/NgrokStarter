import os
import sys
import subprocess
import requests
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QLineEdit, QLabel
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QIcon
import configparser

config = configparser.ConfigParser(interpolation=None)
config.read('config.ini')


class NgrokStarter(QWidget):
    def __init__(self):
        super().__init__()

        self.main_layout = QHBoxLayout()
        self.setLayout(self.main_layout)

        self.left_layout = QVBoxLayout()
        self.right_layout = QVBoxLayout()

        self.main_layout.addLayout(self.left_layout)
        self.main_layout.addLayout(self.right_layout)

        self.port_input = QLineEdit(self)
        self.port_input.setPlaceholderText(f"请输入要映射的端口号，默认{config['default'].get('port')}")
        self.left_layout.addWidget(self.port_input)

        self.start_button = QPushButton('启动', self)
        self.start_button.clicked.connect(self.start_ngrok)
        self.left_layout.addWidget(self.start_button)

        self.stop_button = QPushButton('结束', self)
        self.stop_button.clicked.connect(self.stop_ngrok)
        self.left_layout.addWidget(self.stop_button)

        self.copy_button = QPushButton('复制域名', self)
        self.copy_button.clicked.connect(self.copy_domain)
        self.copy_button.setEnabled(False)
        self.left_layout.addWidget(self.copy_button)

        self.domain_label = QLabel(self)
        self.left_layout.addWidget(self.domain_label)

        self.log_view = QTextEdit(self)
        self.right_layout.addWidget(self.log_view)

        self.resize(800, 600)

        self.thread = None

        self.setWindowTitle("Ngrok Starter")

        # 设置窗口图标，你需要提供一个图标文件的路径
        self.setWindowIcon(QIcon('network.png'))

    def copy_domain(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.domain_label.text())

    def get_domain(self):
        status = 0
        while not status:
            try:
                response = requests.get("http://localhost:4040/api/tunnels")
                public_url = response.json()["tunnels"][0]["public_url"]
                self.domain_label.setText(f"{public_url}")
                status = 1
                self.copy_button.setEnabled(True)
            except Exception as e:
                self.domain_label.setText(str(e))

    def start_ngrok(self):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        port = self.port_input.text()
        if not port:
            port = config['default'].get('port')
        domain = config['default'].get('domain')
        re_path = os.getcwd()
        command = f'{re_path}\\ngrok.exe http --config={re_path}\\ngrok.yml --domain={domain} {port} --log=stdout'
        self.thread = CommandThread(command)
        self.thread.log_signal.connect(self.update_log)
        self.thread.start()
        self.get_domain()

        QApplication.restoreOverrideCursor()

    def stop_ngrok(self):
        os.system("taskkill /f /im ngrok.exe")
        self.thread = None
        self.domain_label.setText("")

    def update_log(self, log):
        self.log_view.append(log)

    def closeEvent(self, event):
        self.stop_ngrok()
        event.accept()


class CommandThread(QThread):
    log_signal = pyqtSignal(str)

    def __init__(self, command):
        super().__init__()
        self.command = command
        self.process = None

    def run(self):
        self.process = subprocess.Popen(self.command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        while True:
            output = self.process.stdout.readline().decode(errors='ignore')
            if output == '' and self.process.poll() is not None:
                break
            if output:
                self.log_signal.emit(output.strip())


if __name__ == '__main__':
    app = QApplication(sys.argv)
    starter = NgrokStarter()
    starter.show()
    sys.exit(app.exec_())
