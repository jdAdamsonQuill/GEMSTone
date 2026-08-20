#!/usr/bin/env python

import json

import asyncio
from websockets.asyncio.server import serve
from websockets.sync.client import connect

import subprocess

import gemst_globals
from gemst_globals import *

#8/24/25 move to gemst_globals.py
#import gemst_constants
#from gemst_constants import *

import gemst_logging
from gemst_logging import log, log_val, log_var

#import gemst_testing
#from gemst_testing import tests

import gemst_utilities
from gemst_utilities import is_equiv, get_timestamp, load_eq_lib, save_eq_lib, reset_eq_lib, to_float, get_obj_list

import gemst_eq_engine
from gemst_eq_engine import update_eq_lib

req_params = {};
dynamic_params = {};
params = {};
lib_id = "default";

async def process_ws(websocket):
    global GUI_ws
    global eq_lib, lib_id
    global OK, ERR
    global req_params, dynamic_params, params

    async for message in websocket:
        datetime = get_timestamp()
        log(f"At {datetime} received message from websocket={websocket}", 'process_ws', level="WS_Activity")

        eq_pos = message.find('=')
            
        if eq_pos > 0:
            kind = message[0:eq_pos]
            log(f"Kind of message:{kind}", 'process_ws', level="WS_Activity")

            data = message[eq_pos+1:]
        else:
            log(f"process_ws() message not of the form 'kind=message'; eq_pos={eq_pos}",
                'process_ws', level='Message_Error')
            return

        # receiving messages like "option=done"
        # send it back for use on their side to facilitate sync and coordination
        if kind == 'option':
            #log(f"Received option of '{data}'", 'process_ws', dbg='Trace', level='Trace')
            if data == "gemst_ws" or data == "load_eq_lib":

                # GUI is up. Tell the param_server this websocket for comms
                #set_GUI_ws(websocket)

                #jda Note: WebSocket in js opens, sends message, then waits for reply
                #          probably to validate the connection. Some "True" response indicates a message is coming.
                log(f"Echoing 'data' to ws", 'process_ws', level="WS_Activity")
                await websocket.send(data)

                eq_lib = load_eq_lib(lib_id=lib_id)

            elif data == "clear_eq_lib":
                eq_lib = {}

            elif data == "list_objects":
                log(f"option={data}", 'process_ws', level="WS_Activity")
                objs = get_obj_list()
                log(f"Sending object list {objs} to ws", 'process_ws', level="WS_Activity")
                await websocket.send(f"objects={objs}")

            elif data == "eq_lib":

                eq_lib_str = str(eq_lib).replace("'", '"')
                eq_lib_str = json.dumps(eq_lib)

                await websocket.send("eq_lib="+eq_lib_str)
                
            elif data == 'done':
                await websocket.send(data)
                log("Received option=done", 'process_ws', level="WS_Activity")
                #jda exit() doesn't work.. how do we quit?

        elif kind == "update":

            params_copy = json.loads(data)
            log(f"kind Update: got params:{params_copy}", 'process_ws', level="WS_Activity")
            params_consts = data

            # 10/3/25 1505 Don't reset.. now recomputing unless user input didn't change the value
            #eq_lib = reset_eq_lib(eq_lib)
                
            for param_name,val_str in params_copy.items():
                val_float = to_float(val_str)
                params.update( {param_name:val_float} );

            eq_lib, params = update_eq_lib( eq_lib, lib_id=lib_id, io_params=params )                

            for param_name,val in params.items():
                params_copy.update( {param_name:str(val)} );

            # Send the params back to the GUI for display update. Don't need to send everything..
            log(f"After update_eq_lib(), sending computed params over websocket: {params}", 
                'process_ws', level="WS_Activity")
            await websocket.send("params="+json.dumps(params_copy) )

        elif kind == "import_eq_lib":
            log(f"Got 'import_eq_lib' command, so calling load_eq_lib({data})",
                'process_ws', level="WS_Activity")

            lib_id = data

            if lib_id is None or lib_id == "tbd" or lib_id == "":
                lib_id = "default"

            eq_lib = load_eq_lib(lib_id=lib_id)

            eq_lib_str = str(eq_lib).replace("'", '"')
            eq_lib_str = json.dumps(eq_lib)

            await websocket.send("eq_lib="+eq_lib_str)

        elif kind == "export_eq_lib":
            log(f"Got 'export_eq_lib' command, so saving eq_lib by: save_eq_lib('{data}')",
                'process_ws', for_summary=True, level='WS_Activity')

            lib_id = data

            saved = save_eq_lib(eq_lib, lib_id=lib_id)
            if saved != OK:
                log(f"Got 'export_eq_lib' but save_eq_lib() failed!", 'process_ws', level='Alert')

        elif kind == "requested_params":
            #log(f"got requested_params={data}", 'process_ws', level="Info")

            req_data = data.replace("'", '"')
            #log(f"after converting tic's to quotes, req_data={req_data}", 'process_ws', level="Info")

            try:
                req_params = json.loads(req_data)
            except Exception as e:
                log(f"Exception on req_params json.loads(req_data={req_data})\n{e}", 'process_ws', level="EXCEPTION")
                return ERR

            #log(f"after json.loads, req_params={req_params}", 'process_ws', "Info")

        elif kind == "dynamic_params":
            try:
                dynamic_params = json.loads(data);
            except Exception as e:
                log(f"Exception on dynamic_params json.loads(data={data})\n{e}", 'process_ws', level="EXCEPTION")
                return ERR

            # Send the dynamic_params back to the GUI for display update. Don't need to send everything..
            log(f"received dynamic_params; sending to the GUI over websocket: {data}", 'process_ws')
            await websocket.send("params="+data )
                
        elif kind == "eq_lib":
            log(f"process_ws() got kind=eq_lib", 'process_ws', dbg="EchoInputs")

            eq_lib_str = data

            try:
                eq_lib = json.loads(eq_lib_str)

                log(f"Current lib_id:{lib_id}; Got updated eq_lib: {json.dumps(eq_lib, indent=4)}", 'process_ws', level="WS_Activity")

            except Exception as e:
                #jda this raises ConnectionClosedOK which is fine.. don't exit
                #TODO Filter exceptions to ingore info messages
                log(f"Exception on json.loads({eq_lib_str})\ne:{e}", 'process_ws', level="EXCEPTION")

            # Updating the library does not save it. After updating memory, Export it to a lib_id to save it.

            params = {}
            params_consts = {}

async def main():
    async with serve(process_ws, "localhost", 8765) as processor:
        await processor.serve_forever()

asyncio.run(main())


