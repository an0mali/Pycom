# -*- coding: utf-8 -*-
"""
Created on Mon Sep 13 11:35:57 2021

@author: Qui
"""

#import multiprocessing
import threading
from Pycom.pycomparse import PycomParse
import socket
import atexit
import time
import sys
#import asyncio

class Pycom(object):
    
    def __init__(self, name, dtbot, sock=None, alivetime=None, mode='server', chunklen=512):
        
        self.name = name
        self.pycomparse = PycomParse('a', self)
        self.chunklen = chunklen
        self.alivetime = alivetime
        self.dtbot = dtbot
        self.hostip = 'localhost'
        self.port = 4432
        
        self.state = ''
        self.new_state = 'connecting'
        self.prev_state = ''
        
        self.verbose = True
        self.prev_frametime = 0.0
        self.serve_thread = False
        self.clientsocket = False
        self.keyboard_kill = False
        self.sending_data = False
        self.rc_file_size = 0
        if alivetime is None:
            self.alivetime = 9999999
        if sock is None:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        else:
            self.sock = sock            
        atexit.register(self.exit_handler)
        self.vprint('Initializing Pycoms')
        #self.process_loop()
        #self.server_proc = multiprocessing.Process(target=self.process_loop)
        self.server_proc = threading.Thread(target=self.process_loop)
        #asyncio.ensure_future(self.process_loop(), loop=self.dtbot.bot.loop)
        self.server_proc.start()
        #asyncio.create_task(self.process_loop)
        print('Pycom initialized')
    
    def _init_connecting(self):
        if not self.serve_thread:
            self.sock.bind((self.hostip, self.port))
            self.sock.listen(1)
            #self.serve_thread = multiprocessing.Process(target=self.server_listen)
           # self.serve_thread.start()            
            self.new_state = 'listen'
        
    def _listen(self, *args):
        try:
            (self.clientsocket, address) = self.sock.accept()
            self.conactive = True
            self.new_state = 'connected'
            self.vprint('Client connected')

        except RuntimeError as e:
            print(e)
            self.new_state = 'listen'
        except KeyboardInterrupt as e:
            self.keykill()
    def set_len(self, newlen):
        if self.chunklen != newlen:
            self.chunklen = newlen
    def keykill(self):
        self.keyboard_kill = True
        self.vprint('Process loop terminated via key command')
        self.exit_handler()
        sys.exit()
    def _init_connected(self):
        print('Client Connected.')
    def _connected(self):
        try:
            self.receive()
            if not self.conactive:
                self.state = 'listen'
                self.vprint('Client has disconnected.')
        except KeyboardInterrupt as e:
            self.keykill()

    def _init_receive_file(self):
        try:
            fdata = self.receive_data()
            if not self.conactive:
                self.state = 'listen'
                self.vprint('Client has disconnected.')
        except KeyboardInterrupt as e:
            self.keykill()
        

    def receive_data(self):
        try:
            count = 0
            while True:
                output = self.get_socket_output(self.rc_file_size)
                count += len(output)
                print('Receieved ' + str(len(output)))
                if count >= self.rc_file_size:
                    break
                
            return output
            
            
            #output = self.pycomparse.clean_received(output)
            #print('\n' + str(output) + '\n')
        except WindowsError as e:
            print(e)
            self.new_state = 'listen'
            
    def process_loop(self):
        while True:
            try:
                ctime = time.time()
                delta = time.time() - self.prev_frametime
                self.prev_frametime = ctime
                statemeth = '_' + self.state
                self.check_and_call(self, statemeth)
                self.change_state()
            except KeyboardInterrupt as e:
                self.keykill()
                
            if self.keyboard_kill:
                self.new_state = 'Terminated'
                break
                
    def send_toclient(self, msg):
        if not self.clientsocket:
            if self.state != 'connected':
                self.pycomparse.pycom_cmd(msg)
            return
       # if self.
       # self.sending_data = True
        stime = time.time()
        totalsent = 0
        mlen = len(msg)
        while True:
            if mlen < self.chunklen:
                msg += ';'
                mlen += 1
            else:
                break
        bmsg = msg.encode('utf-8')
        MSGLEN = len(bmsg)
        #print('Sending message: ' + msg)
        #while MSGLEN < self.chunklen:
         #   msg = str(bmsg.decode('utf-8'))
          #  msg += ';'
           # bmsg = msg.encode('utf-8')
            #MSGLEN = len(bmsg)
        while totalsent < MSGLEN:
            sent = self.clientsocket.send(bmsg[totalsent:])
            if sent == 0:
                self.new_state = 'Terminated'
                raise RuntimeError("socket connection broken")
                
            totalsent = totalsent + sent

        total_time = time.time() - stime
        print("Send time: " + str(total_time))
        #self.sending_data = False
    def receive(self):
        try:
            output = self.get_socket_output()
            output = self.pycomparse.clean_received(output)
            #print('\n' + str(output) + '\n')
        except WindowsError as e:
            print(e)
            self.new_state = 'listen'

    def get_socket_output(self, rcf_size=0):
        chunks = []
        bytes_recd = 0
        chunklen = self.chunklen
        #if rcf_size:
        #    chunklen = int(rcf_size)
        while bytes_recd < chunklen:
            chunk = self.clientsocket.recv(min(chunklen - bytes_recd, chunklen))
            if chunk == b'':
                raise RuntimeError("socket connection broken")
            chunks.append(chunk)
            bytes_recd = bytes_recd + len(chunk)
        inp = b''.join(chunks)
        output = inp.decode('utf-8')

        return output

    def check_and_call(self, obj, statemeth, args=[]):
        if hasattr(obj.__class__, statemeth):
            statefunc = getattr(obj.__class__, statemeth)
            if callable(statefunc):
                if '_init_' in statemeth or '_end_' in statemeth:
                    premes = ':CheckCalls:\tCalling:\t'
                    if '_end_' in statemeth:
                        premes += '_end_: State:\t'
                    else:
                        premes += '_init_: State:\t'
                    premes += self.state
                    self.vprint(premes)
                if len(args):
                    statefunc(obj, args)
                else:
                    statefunc(obj)
                #time.sleep(0.5)
                
    def change_state(self):
        if self.new_state == '':
            return
        ns = self.new_state
        self.new_state = ''
        if ns != self.state:
            self.vprint(':Change_state:\tChanging state to:\t ' + ns)
            end_func = '_end_' + self.state
            self.check_and_call(self, end_func)
            
            self.prev_state = self.state
            self.state = ns
            
            init_func = '_init_' + ns
            self.check_and_call(self, init_func)
    

        
    def vprint(self, mes):
        if self.verbose:
            print('::Pycom::\t' + mes)
                
    def _not_connected(self):
        self.vprint('Not connected')
        
    def exit_handler(self):
        self.vprint('Closing socket connections')
        self.sock.close()
        if self.serve_thread:
            self.serve_thread.terminate()
            self.server_proc.terminate()
            self.server_proc.join()
            self.serve_thread.join()

