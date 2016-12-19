# coding:utf-8
'''Scratch Remote Sensor Connection Library for Python3

Copyright (c) 2015 Daisuke IMAI <hine.gdw@gmail.com>

This software is released under the MIT License.
http://opensource.org/licenses/mit-license.php
'''
from __future__ import (
        absolute_import, division,
        print_function, unicode_literals)
import sys
import types
import socket
import struct
import threading

SCRATCH_HOST = '127.0.0.1' # localhost
SCRATCH_PORT = 42001

class RemoteSensorConnection(object):
    '''Remote Sensor Connection class

    Scratchの遠隔センサ接続を利用するためのクラスです。
    broadcastメッセージはScratch相互に送受信可能
    sensor-updateメッセージは、Scratchからはグローバル変数の変更が送られ、
    このライブラリからScratchへはセンサ値として送られます。

    Usage
         >>> import scratch
         >>> rsc = scratch.RemoteSensorConnection()
         >>> rsc.send_broadcast('gamestart')
    '''

    def __init__(self, receive_broadcast_handler=None, receive_sensor_update_handler=None):
        '''Initialize

        メッセージ受信時の処理のハンドラを指定して、インスタンスを生成します。
        受信処理ハンドラを指定しなくても、インスタンスからメッセージの送信は行えます。
        この時まだ実際にはScratchには接続されません。

        Args:
            receive_broadcast_handler(Optional[function]): broadcastメッセージを受け取った場合のハンドラ
            receive_sensor_update_handler(Optional[function]): sensor-updateメッセージを受け取った場合のハンドラ

        Reises:
            ValueError: receive_broadcast_handler and receive_sensor_update_handler must be function or method
        '''
        self._connected = False
        if receive_broadcast_handler is not None:
            if not (isinstance(receive_broadcast_handler, types.FunctionType) or isinstance(receive_broadcast_handler, types.MethodType)):
                raise ValueError('receive_broadcast_handler must be function or method')
        if receive_sensor_update_handler is not None:
            if not (isinstance(receive_sensor_update_handler, types.FunctionType) or isinstance(receive_sensor_update_handler, types.MethodType)):
                raise ValueError('receive_sensor_update_handler must be function or method')
        self._receive_broadcast_handler = receive_broadcast_handler or self._dummy_broadcast_handler
        self._receive_sensor_update_handler = receive_sensor_update_handler or self._dummy_sensor_data_handler

    def _dummy_broadcast_handler(self, message):
        '''broadcast message dummy handler

        broadcastメッセージを受け取った場合のダミーハンドラです。
        初期化時にハンドラが指定されなければこのハンドラが呼び出されます。

        Args:
            message(str): broadcastメッセージで受け取ったメッセージ
        '''
        pass

    def _dummy_sensor_data_handler(self, **sonsor_data):
        '''sensor-update message dummy handler

        sensor-updateメッセージを受け取った場合のダミーハンドラです。
        初期化時にハンドラが指定されなければこのハンドラが呼び出されます。

        Args:
            **sonsor_data: sendor-updateメッセージで受け取ったグローバル変数名と変数値が渡される。受け取ったあとは辞書として利用できる。
                example:
                    {'sensor_a': 10, 'sensor_b': 20}
        '''
        pass

    def connect(self, host=SCRATCH_HOST, port=SCRATCH_PORT):
        '''Connect to Scratch 1.4 application

        Scratchへの接続を行います。
        Scratch 1.4のアプリケーションを立ち上げ、遠隔センサ接続を有効にした後に接続してください。

        Args:
            host (Optional[str]): Scratchが動作しているIPアドレス(同一のコンピュータでない場合)
            port (Optional[int]): Scratchと接続するポート(通常は指定の必要はありません)

        Raises:
            socket.error: Cannot connect Scratch application
        '''
        if not (isinstance(host, unicode) or isinstance(host, str)):
            raise ValueError('host must be str')
        if not isinstance(port, int):
            raise ValueError('port must be int')
        socket.setdefaulttimeout(1)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.connect((host, port))
        except socket.error as e:
            raise
        self._connected = True
        self._start_receiver()

    def disconnect(self):
        '''Disconnect from Scratch 1.4 application

        Scratchから切断します。
        切断後はSocketは破棄されるので、同一のソケットは利用できません。
        (接続時にソケットの静止をし直すので意識する必要はありません。)

        Raises:
            OSError: something bad
        '''
        if self._connected:
            self._stop_receiver()
            try:
                self.sock.shutdown(socket.SHUT_RDWR)
            except OSError as e:
                raise
            try:
                self.sock.close()
            except OSError as e:
                raise
            self._connected = False

    def is_connected(self):
        '''Check Connection

        Scratchと接続しているかどうかを返します。

        Returns:
            bool: 接続していればTrue、していなければFalse
        '''
        return self._connected

    def _start_receiver(self):
        '''Start Receiver thread
        '''
        self._receiver_alive = True
        self._receiver_thread = threading.Thread(target=self._receiver)
        self._receiver_thread.setDaemon(True)
        self._receiver_thread.start()

    def _stop_receiver(self):
        '''Stop Receiver thread
        '''
        self._receiver_alive = False
        self._receiver_thread.join()

    def _receiver(self):
        '''Receiver
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
                        received_data_len = struct.unpack(">i", receive_buffer[:4])[0]
                        if len(receive_buffer) == 4 + received_data_len:
                            received_data = receive_buffer[4:].decode('utf-8')
                            if received_data.startswith('broadcast'):
                                message = received_data.replace('broadcast ', '', 1).replace('"', '', 2)
                                self._receive_broadcast_handler(message)
                            if received_data.startswith('sensor-update'):
                                sensor_data = received_data.replace('sensor-update ', '', 1).split('"')
                                sensor_data.pop(0)
                                sensor_data_dict = {}
                                while len(sensor_data):
                                    key = sensor_data.pop(0)
                                    value = sensor_data.pop(0).strip()
                                    try:
                                        sensor_data_dict[key] = int(value)
                                    except ValueError:
                                        sensor_data_dict[key] = float(value)
                                self._receive_sensor_update_handler(**sensor_data_dict)
                                pass
                            receive_buffer = b''
        except (OSError, socket.error) as e:
            print('Receiver caught a error.', e, file=sys.stderr)
            print('Receiver thread stoped.')
            raise

    def send_broadcast(self, message):
        '''Send broadcast message

        broadcastメッセージの送信を行います。
        日本語を含むutf-8文字の送信が可能ですが、Scratch側で先にメッセージとして登録していないとScratch側で文字化けします。

        Args:
            message(str): broadcastメッセージとして送信するメッセージ

        Raises:
            ValueError: message must be str
            socket.error: Socket is broken
        '''
        if not (isinstance(message, unicode) or isinstance(message, str)):
            raise ValueError('message must be str')
        message_data = ('broadcast "' + message + '"').encode('utf-8')
        try:
            self.sock.sendall(struct.pack('>i', len(message_data)) + message_data)
        except socket.error as e:
            print('Cannot send broadcast message.', e, file=sys.stderr)
            raise

    def send_sensor_update(self, **sensor_data):
        '''Send sensor-update message

        sensor-updateメッセージの送信を行います。
        センサー名として日本語を含むutf-8文字の送信が可能ですが、Scratch側で先にメッセージとして登録していないとScratch側で文字化けします。
        センサー値は数値(int/float)である必要があります。

        Args:
            **sensor_data: sensor-updateとして送信する、センサー名とセンサー値を、センサー名=センサー値で並べる。任意の数可能
                example:
                    send_sensor_update(sensor_a=10, sensor_b=20)

        Raises:
            ValueError: sensor-value must be str
            socket.error: Socket is broken
        '''
        message = 'sensor-update '
        for name, value in sensor_data.items():
            if not (isinstance(value, int) or isinstance(value, float)):
                raise ValueError('sensor-value must be str')
            message += '"' + name + '" ' + str(value) + ' '
        message_data = message.encode('utf-8')
        try:
            self.sock.sendall(struct.pack('>i', len(message_data)) + message_data)
        except socket.error as e:
            print('Cannot send sensor-update message.', e, file=sys.stderr)
            raise

    def _to_bytes(self, n, length, byteorder='big'):
        h = '%x' % n
        s = ('0'*(len(h) % 2) + h).zfill(length*2).decode('hex')
        return s if byteorder == 'big' else s[::-1]


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
if __name__ == '__main__':

    import time


    class ReceiveHandler(object):
        '''[SAMPLE] Received data handler class
        '''
        @staticmethod
        def broadcast_handler(message):
            print('[receive] broadcast:', message)

        @staticmethod
        def sonsor_update_handler(**sensor_data):
            for name, value in sensor_data.items():
                print('[receive] sensor-update:', name, value)


    print('Scratch Remote Sensor Connection Test')
    print('')

    # Make RemoteSensorConnection instance
    rsc = RemoteSensorConnection(ReceiveHandler.broadcast_handler, ReceiveHandler.sonsor_update_handler)

    # Connect to Scratch 1.4 application
    try:
        rsc.connect()
    except socket.error as e:
        print('Cannot connect Scratch application.', e, file=sys.stder)
        exit()
    time.sleep(2)
    print('[send] broadcast: test_message')
    rsc.send_broadcast('test_message')
    time.sleep(3)
    # send plural values
    print('[send] sensor-update: test_sensor1=0, test_sensor2=0')
    rsc.send_sensor_update(test_sensor1=0, test_sensor2=0)
    time.sleep(3)
    # send fractional value
    print('[send] sensor-update: test_sensor1=0.5')
    rsc.send_sensor_update(test_sensor1=0.5)
    time.sleep(3)
    print('[send] sensor-update: test_sensor1=0')
    rsc.send_sensor_update(test_sensor1=0)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        rsc.disconnect()
