# coding:utf-8
'''Scratch Remote Sensor Connection Library for Python3

Copyright (c) 2015 Daisuke IMAI <hine.gdw@gmail.com>

This software is released under the MIT License.
http://opensource.org/licenses/mit-license.php
'''
import sys
import types
import socket
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

        '''
        if receive_broadcast_handler is not None:
            if not (isinstance(receive_broadcast_handler, types.FunctionType) or isinstance(receive_broadcast_handler, types.MethodType)):
                raise InvalidArgumentsError(sys._getframe().f_code.co_name)
        if receive_sensor_update_handler is not None:
            if not (isinstance(receive_sensor_update_handler, types.FunctionType) or isinstance(receive_sensor_update_handler, types.MethodType)):
                raise InvalidArgumentsError(sys._getframe().f_code.co_name)
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

    def _dummy_sensor_data_handler(self, sonsor_data_dict):
        '''sensor-update message dummy handler

        sensor-updateメッセージを受け取った場合のダミーハンドラです。
        初期化時にハンドラが指定されなければこのハンドラが呼び出されます。

        Args:
            sonsor_data_dict(dict): sendor-updateメッセージで受け取ったメッセージ
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
            socket.
        '''
        if not (isinstance(host, str):
            raise InvalidArgumentsError(sys._getframe().f_code.co_name)
        socket.setdefaulttimeout(1)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.connect((host, port))
        except:
            raise
        self._connected = True
        self._start_receiver()

    def disconnect(self):
        '''Disconnect from Scratch 1.4 application

        Scratchから切断します。
        切断後はSocketは破棄されるので、同一のソケットは利用できません。

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
                        received_data_len = int.from_bytes(receive_buffer[:4], byteorder='big')
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
                                    sensor_data_dict[key] = int(sensor_data.pop(0).strip())
                                self._receive_sensor_update_handler(sensor_data_dict)
                                pass
                            receive_buffer = b''
        except:
            raise

    def send_broadcast(self, message):
        '''Send broadcast message

        broadcastメッセージの送信を行います。
        日本語を含むutf-8文字の送信が可能ですが、Scratch側で先にメッセージとして登録していないとScratch側で文字化けします。

        args:
            message(str): broadcastメッセージとして送信するメッセージ
        '''
        message_data = ('broadcast "' + message + '"').encode('utf-8')
        self.sock.sendall(len(message_data).to_bytes(4, byteorder='big') + message_data)

    def send_sensor_update(self, sensor_data_dict):
        '''Send sensor-update message

        sensor-updateメッセージの送信を行います。
        センサー名として日本語を含むutf-8文字の送信が可能ですが、Scratch側で先にメッセージとして登録していないとScratch側で文字化けします。
        センサー値は数値(int/float)である必要があります。

        args:
            sensor_data_dict(dict): sensor-updateとして送信する、センサー名(str)をキーとしセンサー値(int/float)をバリューとする辞書データ
                example:
                    {'sensor_a': 10, 'sensor_b': 20}
        '''
        message = 'sensor-update '
        for name, value in sensor_data_dict.items():
            message += '"' + name + '" ' + str(value) + ' '
        message_data = message.encode('utf-8')
        self.sock.sendall(len(message_data).to_bytes(4, byteorder='big') + message_data)

class InvalidArgumentsError(Exception):
    '''Invalid Argument Error
    '''
    pass

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
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
