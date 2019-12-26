import socket
import traceback

import paramiko


class SSH(object):
    def __new__(cls, *args, **kwargs):
        paramiko.util.log_to_file("paramiko.log")
        cls.logger = paramiko.util.get_logger("paramiko")
        return super().__new__(cls)

    def __init__(self, host, port, user, password=None):
        self.chan = None
        self.transport = None
        self.is_connect, self.e = self.connect(user, host, port, password)

    def resize(self, cols, rows):
        self.logger.info("重置窗口大小:{},{}".format(cols, rows))
        self.chan.resize_pty(width=cols, height=rows)

    def send(self, msg):
        self.chan.send(msg)

    def read(self):
        return self.chan.recv(10000)

    def close(self):
        self.transport.close()

    def connect(self, user, host, port, password):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((host, port))
        except Exception as e:
            self.logger.error("*** Connect failed: " + str(e))
            traceback.print_exc()

        try:
            self.transport = paramiko.Transport(sock)
            try:
                self.transport.start_client()
            except paramiko.SSHException:
                self.logger.error("*** SSH negotiation failed.")

            self.transport.auth_password(user, password)
            if not self.transport.is_authenticated():
                self.logger.error("*** Authentication failed. :(")
                self.transport.close()

            self.logger.info(f'[secret]--{user}@{host}:{port}')
            self.logger.info(password)

            self.chan = self.transport.open_session()
            self.chan.get_pty(term='xterm')
            self.chan.invoke_shell()
            return True, ''

        except Exception as e:
            self.logger.error("*** Caught exception: " + str(e.__class__) + ": " + str(e))
            return False, str(e)
