# coding:utf-8
'''
Scratch Remote Sensor Connection Library for Python3

Copyright (c) 2015 Daisuke IMAI <hine.gdw@gmail.com>

This software is released under the MIT License.
http://opensource.org/licenses/mit-license.php
'''
import socket
import threading

SCRATCH_HOST = '127.0.0.1' # localhost
SCRATCH_PORT = 42001

class RemoteSensorConnection(object):
    '''
    Remote Sensor Connection class
    '''

    def __init__(self, receive_broadcast_handler=None, receive_sensor_update_handler=None):
        '''
        Initialize
        '''
        socket.setdefaulttimeout(1)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self._receive_broadcast_handler = receive_broadcast_handler or self._dummy_broadcast_handler
        self._receive_sensor_update_handler = receive_sensor_update_handler or self._dummy_sensor_data_handler

    def _dummy_broadcast_handler(self, message):
        pass

    def _dummy_sensor_data_handler(self, sonsor_data_set):
        pass

    def connect(self, host=SCRATCH_HOST, port=SCRATCH_PORT):
        '''
        Connect to Scratch 1.4 application

        Args:
            host (Optional[str]):
            port (Optional[int]):

        Raises:
            socket.
        '''
        try:
            self.sock.connect((host, port))
        except:
            raise
        self._connected = True
        self._start_receiver()

    def disconnect(self):
        '''
        Disconnect from Scratch 1.4 application

        Raises:
            socket.
        '''
        self._stop_receiver()
        try:
            self.sock.shutdown(socket.SHUT_RDWR)
        except:
            raise
        try:
            self.sock.close()
        except:
            raise
        self._connected = False

    def _start_receiver(self):
        '''
        Start Receiver thread
        '''
        self._receiver_alive = True
        self._receiver_thread = threading.Thread(target=self._receiver)
        self._receiver_thread.setDaemon(True)
        self._receiver_thread.start()

    def _stop_receiver(self):
        '''
        Stop Receiver thread
        '''
        self._receiver_alive = False
        self._receiver_thread.join()

    def _receiver(self):
        '''
        Receiver function
        '''
        receive_buffer = b''
        try:
            while self._receiver_alive:
                data =b''
                try:
                    data = self.sock.recv(1)
                except socket.timeout:
                    pass
                if len(data) > 0:
                    receive_buffer += data
                    if len(receive_buffer) >= 4:
                        received_data_len = int.from_bytes(receive_buffer[:4], byteorder='big')
                        if len(receive_buffer) == 4 + received_data_len:
                            received_data = receive_buffer[4:].decode('utf-8')
                            if received_data.startswith('broadcast'):
                                message = received_data.replace('broadcast ', '', 1).replace('"', '', 2)
                                self._receive_broadcast_handler(message)
                            if received_data.startswith('sensor-update'):
                                print(receive_buffer[4:])
                                sensor_data = received_data.replace('sensor-update ', '', 1).split('"')
                                sensor_data.pop(0)
                                sensor_data_dict = {}
                                while len(sensor_data):
                                    key = sensor_data.pop(0)
                                    sensor_data_dict[key] = int(sensor_data.pop(0).strip())
                                self._receive_sensor_update_handler(sensor_data_dict)
                                pass
                            receive_buffer = b''
        except:
            raise

    def send_broadcast(self, message):
        '''
        Send broadcast message

        args:
            message(str):
        '''
        message_data = ('broadcast "' + message + '"').encode('utf-8')
        self.sock.sendall(len(message_data).to_bytes(4, byteorder='big') + message_data)

    def send_sensor_update(self, sensor_data_dict):
        '''
        Send sensor-update message

        args:
            sensor_data_dict(dict):
                example:
                    {'sensor_a': 10, 'sensor_b': 20}
        '''
        message = 'sensor-update '
        for name, value in sensor_data_dict.items():
            message += '"' + name + '" ' + str(value) + ' '
        message_data = message.encode('utf-8')
        print(message_data)
        self.sock.sendall(len(message_data).to_bytes(4, byteorder='big') + message_data)


if __name__ == '__main__':

    import time

    class ReceiveHandler(object):
        '''[SAMPLE] Received data handler class
        '''
        def broadcast_handler(self, message):
            print('[receive] broadcast:', message)

        def sonsor_update_handler(self, sensor_data_dict):
            for name, value in sensor_data_dict.items():
                print('[receive] sensor-update:', name, value)

    rh = ReceiveHandler()
    rsc = RemoteSensorConnection(rh.broadcast_handler, rh.sonsor_update_handler)
    rsc.connect()
    time.sleep(2)
    rsc.send_broadcast('TEST')
    time.sleep(4)
    rsc.send_sensor_update({'TEST': 0, "TEST2": 0})
    time.sleep(4)
    rsc.send_sensor_update({'TEST': 100, "TEST2": 0})
    time.sleep(4)
    rsc.send_sensor_update({'TEST': 0, "TEST2": 0})
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        rsc.disconnect()
