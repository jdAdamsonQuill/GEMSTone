import sys

import asyncio
from websockets.asyncio.server import serve

#####
# Here’s how a client sends and receives messages with the threading API:

#!/usr/bin/env python

import gemst_globals
from gemst_globals import *

import gemst_utilities
from gemst_utilities import load_param_lib, load_eq_lib

from websockets.asyncio.server import serve
from websockets.sync.client import connect

#async def echo(websocket):
#    async for message in websocket:
#        await websocket.send(message)
def hello():
    with connect("ws://localhost:8765") as websocket:
        websocket.send("Hello world!")
        message = websocket.recv()
        print(f"Received: {message}")

def ws_recv_msg(websocket):
    done = False
    while not done:
        message = websocket.recv()
        #print(f"we_recv_msg() Received: {message}")
        if message == "done":
            break

async def send_eq_lib(eq_lib):
    #with connect("ws://localhost:8765") as websocket:
    with connect("ws://localhost:8765/socket") as websocket:
        print(f"send_eq_lib: to ws 8765, sending eq_lib")
        websocket.send( 'option=reset_eq_lib' )
        websocket.send( 'eq_lib="'+eq_lib+'"' )

async def send_param_lib(param_lib):
    #with connect("ws://localhost:8765") as websocket:
    with connect("ws://localhost:8765/socket") as websocket:
        print(f"send_param_lib: to ws 8765, sending param_lib={param_lib}")
        websocket.send( 'param_lib="'+param_lib+'"' )

        #ok.. testing i/f w/ firefox
        #websocket.send( "option=done" )
        #ws_recv_msg(websocket)

def send_requested_params( requested_params ):
    with connect("ws://localhost:8765/socket") as websocket:
        websocket.send('requested_params='+requested_params)

#async def main():
#    async with serve(ws_recv_msg, "localhost", 8767) as server:
#        await server.serve_forever()

param_lib = {}
param_lib = load_param_lib()
options = {'scale':'default','units':'cradian'}
str_opts = str(options)
req_params = {'dx':options,'dt':options,'v':options}
str_req_params = str(req_params)

#send_requested_params( str_req_params )
#asyncio.run(send_param_lib(str(param_lib)))

def xmit_eq_lib():
    global eq_lib
    eq_lib = load_eq_lib()
    asyncio.run(send_eq_lib(str(eq_lib)))

#xmit_eq_lib()

#asyncio.run(main())

#hello()

def interact():

    # sys.argv is a list where:
    # sys.argv[0] is the script name itself
    # sys.argv[1] is the first argument, sys.argv[2] is the second, and so on.

    if len(sys.argv) > 1:
        command = sys.argv[1]
        print(f"Processing command: {command}")
        with connect("ws://localhost:8765/socket") as websocket:
            websocket.send(command)
    else:
        done = False 
        while not done:
            command = input("Command (option=data)? ")
            if command == "done" or command == "quit" or command == "exit":
                done = True
                return
            elif command == "help":
                print(f"usage: option=<the_option>, or keyword=data; quit/exit/done to end.")
                print(f"e.g.: cmd=update  // calls compute_all to update eq_lib")

            print(f"Processing command: {command}")
            with connect("ws://localhost:8765/socket") as websocket:
                websocket.send(command)

interact()

