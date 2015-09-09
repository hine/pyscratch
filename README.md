# pyscratch

## Overview

This module make easier to use Scratch Remote Connection from Python 2.7.  

if you use with Python3, see [master branch](https://github.com/hine/pyscratch/tree/master).

## Installation

$ git clone -b 2.7 git@github.com:hine/pyscratch.git  
$ cd pyscratch  
$ pip install .  

## Usage

example:  
```py
import scratch
class ScratchReceiver(object):
  @staticmethod
  def broadcast_handler(message):
    print('[receive] broadcast:', message)
  @staticmethod
  def sonsor_update_handler(\*\*sensor_data):
    for name, value in sensor_data.items():
      print('[receive] sensor-update:', name, value)
rsc = RemoteSensorConnection(ScratchReceiver.broadcast_handler, ScratchReceiver.sonsor_update_handler)  
rsc.connect()  
rsc.send_broadcast('connected')  
rsc.send_sensor_update(test_sonsor=100)  
rsc.disconnect()  
```

## Documentation

PyDoc Documents are in "docs" directory.  

## License
This software is released under the MIT License, see LICENSE file.
