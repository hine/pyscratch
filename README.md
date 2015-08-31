# pyscratch

## Overview

This module make easier to use Scratch Remote Connection from Python3.  

## Installation

$ git clone git@github.com:hine/pyscratch.git  
$ cd pyscratch  
$ pip install .  

## Usage

example:  
```py
import scratch
class ReceiveHandler(object):
  def broadcast_handler(self, message):
    print('[receive] broadcast:', message)
  def sonsor_update_handler(self, \*\*sensor_data):
    for name, value in sensor_data.items():
      print('[receive] sensor-update:', name, value)
rh = ReceiveHandler()  
rsc = RemoteSensorConnection(rh.broadcast_handler, rh.sonsor_update_handler)  
rsc.connect()  
rsc.send_broadcast('connected')  
rsc.send_sensor_update(test_sonsor=100)  
rsc.disconnect()  
```

## Documentation

PyDoc Documents are in "docs" directory.  

## License
This software is released under the MIT License, see LICENSE file.
