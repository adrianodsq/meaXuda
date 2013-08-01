import tornado.httpserver
import tornado.websocket
import tornado.ioloop
import tornado.web
import subprocess
import os
import json
import time

class WSHandler(tornado.websocket.WebSocketHandler):
    waiters = set()
    objbuffer = ''
    hashUsers = {}
    masterSession = {}
    errorBuffer = []
    codeBuffer = []
   
    def open(self):
        print 'new file connection'
        #print self.request
        if len(WSHandler.errorBuffer) != 0:
            obj = json.dumps(WSHandler.errorBuffer)
            self.write_message(obj)
        if len(WSHandler.codeBuffer) != 0:
            obj = json.dumps(WSHandler.codeBuffer)
            self.write_message(obj)
        #self.write_message(WSHandler.objbuffer)
             
    def on_close(self):
        print 'connection file closed'
        flag = 1
        for key, users in WSHandler.hashUsers.items():
            for user in users:
	        if user == self:
                    #print 'encontou!'
                    flag = 0
		    break
    	    if flag == 0:
	        break
        if flag == 0:
            WSHandler.hashUsers[key].remove(self)
                
            if len(WSHandler.hashUsers[key]) == 0:
   	        del WSHandler.hashUsers[key]
                del WSHandler.masterSession[key]
                os.system('rm -r /home/ftp/sdFiles/'+key)
        
            else:
                #print 'master: ',WSHandler.masterSession[key]
                #print 'user: ', user
                #print 'self: ', self
                if self == WSHandler.masterSession[key]:
                    WSHandler.masterSession[key] = WSHandler.hashUsers[key].pop()
                    WSHandler.hashUsers[key].add(WSHandler.masterSession[key])
                    newMaster = json.dumps('MA')
                    WSHandler.masterSession[key].write_message(newMaster)
      
    @classmethod
    def send_updates(cls, compact, key, self):
        obj = json.dumps(compact)
        #print compact[0]
        #print 'self->'
	    #print self
        for users in cls.hashUsers[key]:
            #print 'user->'
	        #print users
	    if compact[0] == 'C': 
                if self != users:  #arrumar  
                    #print 'oi'
                    users.write_message(obj)
            
            else:
                users.write_message(obj)
            
    
    def on_message(self, message):
        infoConnect = json.loads(message)

        if infoConnect[0] == 'N':
	    #print infoConnect[1]
            liveDir = subprocess.Popen('sh verificaDir.sh '+infoConnect[1],shell=True, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
            output, errors = liveDir.communicate()
            if output[0] == '0':
                WSHandler.hashUsers[infoConnect[1]] = set([self])
                WSHandler.masterSession[infoConnect[1]] = self;
                os.system('sh criaDir.sh '+infoConnect[1])
                #repsKey = json.dumps(['K',)
	        #self.write_message(respKey)
	        print 'diretorio criado'
               
            else:
	        #WSHandler.hashUsers[infoConnect[1]].add(self)
		#self.write_message('1')
                print 'diretorio ja existe'
            
            #print WSHandler.hashUsers.items()
	    respKey = json.dumps(['NS', output[0]])
            self.write_message(respKey)
            respKey = json.dumps('MA')
            self.write_message(respKey)    

        else:
            if infoConnect[0] == 'S':
                liveDir = subprocess.Popen('sh verificaDir.sh '+infoConnect[1], shell=True, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
                output, errors = liveDir.communicate()
                if output[0] == '1':
                    WSHandler.hashUsers[infoConnect[1]].add(self)
                
                respKey = json.dumps(['SS', output[0]])
                self.write_message(respKey)
                
            else:
	        #logging.info("got message %r", message)
                #print 'message received %s' % message
                #print self
                #self.write_message(message)
                WSHandler.objbuffer = infoConnect[2]
                #WSHandler.MakeFile (self,infoConnect[0],infoConnect[1],infoConnect[3])
                compactCode = ['C',infoConnect[2]]
                WSHandler.codeBuffer = compactCode 
                WSHandler.send_updates(compactCode,infoConnect[3],self)
                WSHandler.MakeFile (self, infoConnect[0], infoConnect[1], infoConnect[3])
 
    def MakeFile (self, nameNoExt, name, dir):
        key = dir
        shFile =  nameNoExt+'.sh'
	file = open('/home/ftp/sdFiles/'+dir+'/'+name, 'w')
        file.write(WSHandler.objbuffer)
        file.close()
        file = open('/home/ftp/sdFiles/'+dir+'/'+shFile,'w')
        file.write('#!/bin/sh\nstring=$(gcc -o /home/ftp/sdFiles/'+dir+'/'+nameNoExt+' /home/ftp/sdFiles/'+dir+'/'+name+')\necho "$string"')
        file.close()
        resp = subprocess.Popen('sh /home/ftp/sdFiles/'+dir+'/'+shFile, shell=True, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
        output , errors = resp.communicate()
        if len(errors) == 0:
            compactResp = ['O', name, nameNoExt]
        
        else:
            compactResp = ['E', errors, name]
            WSHandler.errorBuffer = compactResp
        
        WSHandler.send_updates(compactResp,key,self)
                
class WSChat(tornado.websocket.WebSocketHandler):
    waiters = set()
    objbuffer = ''
    hashUsers = {}
    timeFlood = {}

    def open(self):
        print 'new chat connection'
        #WSChat.waiters.add(self)
        #self.write_message(WSHandler.objbuffer)
             
    def on_close(self):
        print 'chat connection closed'
        #WSChat.waiters.remove(self)
        flag = 1
        for key, users in WSChat.hashUsers.items():
            for user in users:
	        if user == self:
                    #print 'encontou!'
                    flag = 0
		    break
    	    if flag == 0:
	        break
        if flag == 0:
            WSChat.hashUsers[key].remove(self)
            if len(WSChat.hashUsers[key]) == 0:
   	        del WSChat.hashUsers[key]
    
    @classmethod
    def send_updates(cls, objMsg, key, self):
        #logging.info("Enviado para %d", len(cls.waiters))
        for users in cls.hashUsers[key]:
            if self != users:
                users.write_message(objMsg)
    
    def on_message(self, message):
        #logging.info("got message %r", message)
        infoMessage = json.loads(message)

        print infoMessage
        
        if infoMessage[0] == 'N':
            if WSChat.hashUsers.has_key(infoMessage[1]) == False:
                WSChat.hashUsers[infoMessage[1]] = set([self])
                WSChat.timeFlood[self] = 0.0
        
        else:
            if infoMessage[0] == 'S':
                if WSChat.hashUsers.has_key(infoMessage[1]) == True:   
                    WSChat.hashUsers[infoMessage[1]].add(self)
                    WSChat.timeFlood[self] = 0.0
            
            else:
                if infoMessage[0] == 'SPAN':
                    WSChat.NoFlood(self)
                    WSChat.timeFlood[self] = time.time()

                else:
                    WSChat.NoFlood(self)
                    WSChat.timeFlood[self] = time.time()
                    compactMessage = json.dumps([infoMessage[2],infoMessage[3]])
                    WSChat.send_updates(compactMessage, infoMessage[1],self)

    def NoFlood(self):
        timeLastMsg = time.time() - WSChat.timeFlood[self]
        if timeLastMsg < 0.35:
            self.write_message(json.dumps(['F']))
        
        if timeLastMsg > 15.0:
            self.write_message(json.dumps(['NF']))   
        
application = tornado.web.Application([
    (r'/wsFile', WSHandler),
    (r'/wsChat', WSChat),
])
 
if __name__ == "__main__":
    os.system('rm -r /home/ftp/sdFiles/*')
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(9002)
    tornado.ioloop.IOLoop.instance().start()
