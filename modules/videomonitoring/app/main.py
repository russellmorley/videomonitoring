# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import time
import os
import sys
import asyncio
import concurrent.futures
from six.moves import input
import threading
from azure.iot.device.aio import IoTHubModuleClient
from videostreamserver import VideoStreamServer
import signal

from types import SimpleNamespace
class IoTHubModuleClient_Mock(object):
    @staticmethod
    def create_from_edge_environment():
        return IoTHubModuleClient_Mock()

    async def receive_message_on_input(self, id):
        await asyncio.sleep(30)
        return SimpleNamespace(
            data = 'The Data', 
            custom_properties = 'The Custom Properties'
        )

    async def send_message_to_output(self, x, y):
        pass

    async def connect(self):
        pass

    async def disconnect(self):
        pass

async def main():
    try:
        if not sys.version >= "3.5.3":
            raise Exception( "Requires python 3.5.3+. Current version of Python: %s" % sys.version )

        # The client object is used to interact with your Azure IoT hub.
        module_client = IoTHubModuleClient_Mock.create_from_edge_environment()

        # connect the client.
        await module_client.connect()

        # define behavior for receiving an input message on controlinput
        async def controlinput_listener(module_client):
            while True:
                control_message = await module_client.receive_message_on_input("controlinput")  # blocking call
                print("the data in the message received on controlinput was ")
                print(control_message.data)
                print("custom properties are")
                print(control_message.custom_properties)
                print("forwarding mesage to output1")
                await module_client.send_message_to_output(control_message, "control message response")

        # define behavior for halting the application

        def stdin_listener():
            while True:
                try:
                    selection = input("PRESS Q TO QUIT (ignore Flask ctrl-c message) \n")
                    if selection == "Q" or selection == "q":
                        print("Quitting...")
                        return
                except:
                    time.sleep(10)

        video_stream_server = VideoStreamServer()

        '''
        def signal_handler(sig, frame):
                print('You pressed Ctrl+\!')
                video_stream_server.stop()
        signal.signal(signal.SIGQUIT, signal_handler)
        '''

        # Schedule task for C2D Listener
        print ( "Starting listening for IoTEdge controlinput messages... ", end='')
        listeners = asyncio.gather(controlinput_listener(module_client))
        print ( 'done.')

        loop = asyncio.get_event_loop()
        #with concurrent.futures.ThreadPoolExecutor() as pool:
        await loop.run_in_executor(None, video_stream_server.start)
        await loop.run_in_executor(None, stdin_listener)
        await loop.run_in_executor(None, video_stream_server.stop)

        print("Stopping listening for IoTEdge controlinput messages...", end='')
        # Cancel listening
        listeners.cancel()
        print('done.')

        print("Disconnecting from IoTEdge...", end='')
        # Finally, disconnect
        await module_client.disconnect()
        print('done.')

        print("Shutdown complete.")

    except Exception as e:
        print ( "Unexpected error %s " % e )
        raise

if __name__ == "__main__":

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()

    # If using Python 3.7 or above, you can use following code instead:
    #asyncio.run(main())


