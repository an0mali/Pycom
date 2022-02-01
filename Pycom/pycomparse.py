# -*- coding: utf-8 -*-
"""
Created on Mon Sep 13 11:35:57 2021

@author: Qui
"""
import os
class PycomParse(object):

    def __init__(self, name, pycom):
        self.name = name
        self.pycom = pycom
        self.verbose = True

    def clean_received(self, output):
        #In our protocol we use ';^' to denote the end of message and ';' to fill empty space
        if output[-1] == ';':
                split = output.split(';^')
                output = split[0]

        elif output[-1] == '|':
            output = output.replace('|', '')
        if output[0] == '|':
            self.pycom_cmd(output)
        return output
    def vprint(self, mes):
        if self.verbose:
            print('::PycomParse::\t' + mes)
    def pycom_cmd(self, output):
        #print('Pycom_cmd:: Received: ' + output)
        output = output.replace('|', '')
        parts = output.split(',')
        cmd = parts[0]
        cargs = []
        for part in parts:
            if part != cmd:
                cargs.append(part)
        
        #print('Detected command: ' + cmd + ' with args: ' + str(cargs))
        if self.pycom.state != 'connected':
            self.discord_response("Ultimate Turtle Simulator is not currently online. Try again later.&" + cargs[1])
            return
        self.pycom.check_and_call(self, cmd, str(cargs))
        
        

    def discord_response(self, *args):
        
        asplit = args[0].split("&")
        #print(str(asplit))
        ctxid = 'all'
        if len(asplit) > 1:
            
            ctxid = asplit[1]
            ctxid = ctxid.replace("']", '')
            ctxid = ctxid.replace(';', '')
            ctxid = ctxid.replace('discord_response', '')
        res = asplit[0]
        res = self.format_res(res)
        self.vprint('Discord response: ' + str(res))
        self.pycom.dtbot.send_to(res, ctxid, True)
        #if self.pycom.chunklen != setlen:
         #   self.pycom.chunklen = setlen
    def receive_file(self, res):
        res = self.format_res(res)
        res = res.replace(']', '')
        res = res.split(', ')
        #print('\nReceive file path: ' + res[0] + ' \nctxid: ' + res[1] + '\nusrid: ' + res[2])
        fpath = res[0]
        usrid = res[2]
        ctxid = res[1]
        
        usrid = usrid.replace(' ', '')
        ctxid = ctxid.replace(' ', '')
        ctxid = ctxid.replace(';', '')
        print(fpath)
        print(usrid)
        print(ctxid)
        slist = self.pycom.dtbot.user_screens
        rmlist = self.pycom.dtbot.rm_usrscreen
        if len(rmlist):
            for p in rmlist:
                p = os.path.expandvars(p)
                try:
                    os.remove(p)
                except:
                    pass
        rmlist.clear()
        ssinfo = [fpath, ctxid]
        if not usrid in slist:
            slist[usrid] = []

        slist[usrid].append(ssinfo)
        try:
            if len(slist[usrid]) > 10:
                item = slist[usrid].pop(0)
                os.remove(item[0])
        except:
            pass
        
        #slist[usrid].append(ssinfo)

    def end_rc_file(self, *args):
        self.pycom.new_state = 'connected'
        self.pycom.chunklen = 512

    def format_res(self, res):
        res = res.replace("['", '')
        res = res.replace("'", '', len(res) -1)
        #res = res.replace("]", '', len(res) -1)
        return res