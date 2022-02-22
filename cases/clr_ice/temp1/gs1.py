#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import threading
import subprocess
#import shlex
import time
import socket
import struct
from enum import Enum,IntEnum #, Enum, unique

Debug=False


def gs1_reader(self,functor):
	if Debug: print ('gs1_reader start')
	while (not self.stopcallback):
		msg=self.read_msg(True)
		if(msg['command']<0):
			time.sleep(1)
			if (not self.stopcallback):
				print ('Error in gs1_reader: can\'t take msg')
		else:
			functor(msg)
	if Debug: print ('gs1_reader stop')

class commands(IntEnum):
	ERR = -1
	HELP = 0
	STOP = 1
	EXIT = 1
	QUIT = 1
	READ_INFO = 2
	DISTRIBUTE = 3
	READ_MESH = 4
	READ = 5
	SET_SOLVER = 6
	SET_DATA_PARAM = 7
	SET_ZONE_PARAM = 8
	SET_BOUNDARY_PARAM = 9
	WRITE_INFO = 10
	WRITE_MESH = 11
	WRITE = 12
	WRITE_STATIC = 13
	WRITE_DYNAMIC = 14
	EXTEND_MESH = 16
	INIT_STATIC = 23
	INIT_DYNAMIC = 30
	SET_TIMESTEP = 31
	SET_DT = 32
	SET_TIME = 33
	READ_DYNAMIC = 34
	READ_STATIC = 40
	CALC_ITERATION = 41
	CALC_ITERATE = 42
	IMPORT = 43
	EXPORT = 44
	#EXPORT_PLOT3D_DYNAMIC = 45
	SYNC = 46
	PARALLEL_SETTINGS = 47
	COMMAND_QUEUE_CLEAN = 48
	COMMAND_QUEUE_CLEAN_AND_BREAK = 49
	COMMAND_QUEUE_GET_PROGRESS = 50
	COMMAND_QUEUE_BREAK = 51
	COMMAND_QUEUE_GET_LIST = 52
	GUI_GET_GL = 53
	GUI_UPDATE_GL = 54
	GET_MODEL_INFORMATION = 55
	FS_LS = 56
	FS_MOVE = 57
	FS_MKDIR = 58
	GET_SOLVER_INFORMATION = 59
	FS_COPY = 60
	FS_RM = 61
	SET_PROBE = 62
	GET_PROBES = 63
	GET_PROBES_INTEGRALS = 64
	GET_PROBE_FIELDS = 65
	GET_CONTROLS = 66
	SET_WD = 67

	COMMAND_QUEUE = 500
	COMMAND_QUEUE_PROGRESS = 501
	GUI_SUMMARY = 502
	GUI_OBJECT = 503
	MODEL_INFORMATION = 504
	MODEL_OBJECT = 505
	FS_LS_MSG = 506
	FS_MKDIR_MSG = 507
	SOLVER_INFORMATION = 508
	UPDATE_DATA_INFORMATION = 509
	UPDATE_ZONE_INFORMATION = 510
	UPDATE_BOUNDARY_INFORMATION = 511
	FS_MOVE_MSG = 512
	FS_COPY_MSG = 513
	FS_RM_MSG = 514
	PROBE_INFO = 515
	PROBE_INTEGRALS = 516
	PROBE_FIELD = 517
	MODEL_FINISH = 509
	GL_INFO = 600
	PROBE_FIELD_BIN = 601

class reduct(Enum):
	MAX = "MAX"
	MIN = "MIN"
	MUL = "MUL"
	SUM = "SUM"
	AVE = "AVE"

class solver_type(Enum):
	NONE = "NONE"
	FLUID = "FLUID"
	SOLID = "SOLID"

class boundary_direction(Enum):
	I0 = "I0"
	J0 = "J0"
	K0 = "K0"
	I1 = "I1"
	J1 = "J1"
	K1 = "K1"

class solverdata_type(Enum):
	NODE = "NODE"
	CORE = "CORE"

class field_type(Enum):
	NODE = "NODE"
	CORE = "CORE"
	B_I = "B_I"
	B_J = "B_J"
	B_K = "B_K"
	E_I = "E_I"
	E_J = "E_J"
	E_K = "E_K"

class field_class(Enum):
	UNKNOWN = "UNKNOWN"
	INT = "INT"
	FLOAT = "FLOAT"
	FLAGS = "FLAGS"
	POINTER = "POINTER"

class precision(Enum):
	DIFFERENT = "DIFFERENT"
	SINGLE = "SINGLE"
	DOUBLE = "DOUBLE"


class probe_field_type(Enum):
	NODE = "NODE"
	CORE = "CORE"
	FACE = "FACE"
	EDGE = "EDGE"

class export_type(Enum):
	AUTO = "AUTO"
	PFGIBC = "PFGIBC"
	GRIDPRO = "GridPRO"
	PLT = "PLT"



# класс реализует протокол общения с сервером
class gs1_supersock:
	attempts_count=30
	main_size=32
	zircon_cmd = r'D:\zircon_dist\2022.02.21\bin\solver_vs13.exe'
	#zircon_cmd = self.version
	#zircon_cmd = r'C:\zircon\projects\solver.vs\solver_vs13\x64\Debug\solver_vs13.exe'
	zircon_env = {"PYTHONHOME" : r"D:\zircon_dist\Python35x64","PYTHONPATH" : r"D:\zircon_dist\Python35x64;D:\zircon_dist\Python35x64\DLLs;D:\zircon_dist\Python35x64\Lib;D:\zircon_dist\Python35x64\Lib\site-packages","PATH": r"D:\zircon_dist\Python35x64;C:\Program Files (x86)\IntelSWTools\mpi\2019.5.281\intel64\bin\release","I_MPI_FABRICS":"shm","SystemRoot":"C:\Windows"}
	#zircon_cmd = 'echo'
	mpi_cmd = 'mpiexec.hydra'

	def get_free_localport(self):
		mas = range(32000, 65000)
		host = "127.0.0.1"
		for port in mas:
			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			# s.settimeout(1)
			try:
				s.bind((host, port))
			except socket.error as msg:
				if Debug: print('Bind failed. Port =', port, 'Error Code : ' + str(msg))
			else:
				s.close()
				return port
			s.close()
		return -1

	def read_msg(self,fromcallback=False,nolock=False): # функция считывает из сокета одно сообщение и возвращает его или ошибку

		param_size=0
		main_readed=False
		read_main_bytes=0
		read_param_bytes=0
		main_data=bytes(0)
		param_data=bytes(0)
		command=-1
		while ((not self.stoprader) or (read_main_bytes != 0)): # ни в коем случае нельзя прерывать чтение посередине пакета - следующий будет читать не то что ожидает - какой-то кусок данных
			try:
				if( not main_readed):
					bytes_to_recv=self.main_size-read_main_bytes
	#				print("recv1")
					if ( not nolock ): self.lock_reader()
					data=self.sock.recv(bytes_to_recv)# тут сработает исключение socket.timeout или socket.error
					bytes_recv=len(data)
					if bytes_recv == 0 : # чтение из закрытого сокета-не ошибка, поэтому проверяем что данные идут, если их нет - соединение прервано
						raise Exception("Connection lost")
					read_main_bytes+=bytes_recv
					main_data+=data
					if (read_main_bytes == self.main_size ):
						inform = struct.unpack(self.mainstruct,main_data)
						if Debug: print(inform)
						command=inform[0]
						param_size=inform[1]
						if(param_size>0):
							main_readed=1
							read_param_bytes=0
							param_data=bytes(0)
						else:
							#process_script_node
							if ( not nolock ): self.release_reader()# все данные получены - разблокируем чтение
							if Debug: print("Accept command ",inform[0]," without data")
							break
				else:# читаем пакеты с дополнительными параметрами
					bytes_to_recv=param_size-read_param_bytes
	#				print("recv2")
					data=self.sock.recv(bytes_to_recv)# тут сработает исключение socket.timeout или socket.error
					bytes_recv=len(data)
					if bytes_recv == 0 :
						raise Exception("Connection lost")
					read_param_bytes+=bytes_recv
					param_data+=data
					if (read_param_bytes == param_size ):
						if ( not nolock ): self.release_reader()# все данные получены - разблокируем чтение
						inform = struct.unpack(self.mainstruct,main_data)
						if Debug: print("Accept command ",inform[0]," with data: ",param_data)
						break

			except socket.timeout:
				if (read_main_bytes==0): # если данные не пришли, то не будем держать блокировку
					if ( not nolock ):
						self.release_reader()
						time.sleep(0.04) # вызовем прерывание, чтобы другие потоки могли захватить блокировку
						if Debug: print("Sleep without messaeges")
					if (fromcallback and self.stopcallback):
						break

	#			print('#')
				continue
			except socket.error as e:
				# в случае сбоя сокета выкинем недополученные данные
				command=-1
				param_size=0
				main_readed=False
				read_main_bytes=0
				read_param_bytes=0
				main_data=bytes(0)
				param_data=bytes(0)
				if ( not nolock ): self.release_reader() # наверняка ошибка вызвана сокетом, а перед этим мы блокировали чтение
				print('Error in gs1_reader: ',e)
				break
			except Exception as e:
				# в случае сбоя сокета выкинем недополученные данные
				command=-1
				param_size=0
				main_readed=False
				read_main_bytes=0
				read_param_bytes=0
				main_data=bytes(0)
				param_data=bytes(0)
				if ( not nolock ): self.release_reader() # разблокируем чтение
				print('Error in gs1_reader: ',str(e))
				break
			except :
				command=-1
				param_size=0
				main_readed=False
				read_main_bytes=0
				read_param_bytes=0
				main_data=bytes(0)
				param_data=bytes(0)
				if ( not nolock ): self.release_reader() # разблокируем чтение
				print('Error in gs1_reader unknown error')
				break
		if Debug: print('reader stoped')
#		if (read_main_bytes == main_size ):
		return {'command':commands(command),'paramsize':param_size,'main':main_data,'param':param_data}
#		else
#			return {'command':command}

	def send_simple(self,command):
		try:
			data = struct.pack(self.mainstruct, command.value, 0, 0, 0, 0, 0, 0, 0)
			return (self.sock.send(data)==self.main_size)
		except socket.error as e:
			print ("Error sending to socket")
			return False


	def send_dict(self,command,dict):
		try:
			param_data=bytes(str(dict)+"\0","utf-8")
			param_data_size=len(param_data)
			data = struct.pack(self.mainstruct, command.value, param_data_size, 0, 0, 0, 0, 0, 0)
			if Debug: print('send_dict main:',data)
			if Debug: print('send_dict data:',param_data)
			if (self.sock.send(data)==self.main_size):
				if (self.sock.send(param_data) == param_data_size):
					return True
			print("Error 1 sending dict to socket")
			return False
		except socket.error as e:
			print ("Error 2 sending dict to socket")
			return False

	def start_callback_msg(self,functor):
		self.stop_callback_msg()
		self.stopcallback=False
		self.reader = threading.Thread(target=gs1_reader, args=(self,functor))
		self.reader.start()

	def stop_callback_msg(self):
		try:
			self.stopcallback=True
			self.reader.join()
		except :
			pass


	def run_local_solver(self,path,port=-1,version=None): # запустим солвер в указанном каталоге и подключаемся к нему

		if not (version is None):
			self.zircon_cmd = version
		if (port<0): port=self.get_free_localport()
		if Debug: print("run_local_solver port", port)
		if (port>=0):
			cmd=self.zircon_cmd+" -P "+str(port)
			if Debug: print("run_local_solver cmd", cmd)
			ofile=os.path.join(path, "gs1_"+str(port)+".out.txt")
			if Debug: print("run_local_solver ofile", ofile)
			efile=os.path.join(path, "gs1_"+str(port)+".err.txt")
			if Debug: print("run_local_solver efile", efile)
			newenv = os.environ.copy()
			envitems = self.zircon_env.items()
			for key,val in envitems:
				if key in newenv.keys():
					newenv[key]=val + os.pathsep + newenv[key]
				else:
					newenv[key] = val
			if Debug: print("run_local_solver env", newenv)
			subprocess.Popen(cmd, env=newenv, shell=True,stdout=open(ofile,'w+'), stderr=open(efile,'w+'),stdin=subprocess.DEVNULL,cwd=path)
			return self.connect_to_socket("127.0.0.1",port)
		else:
			return False

	def connect_to_socket(self,host,port): # соединяемся с AF_INET сокетом программы напрямую
		attempts=self.attempts_count
		while attempts>0:
			attempts=attempts-1
			if Debug: print ("gs1_supersock connect_to_socket",host,port)
			try:
				self.sock_activated=False
				self.reader_activated=False
				self.stoprader=False
				self.sock = socket.socket()
				self.sock.settimeout(1)
				self.sock.setsockopt( socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
				self.sock.connect( (host, port) )
			except socket.timeout:
				if Debug: print ("gs1_supersock TimeOut connect to socket")
			except socket.error as e:
				if Debug: print ("gs1_supersock Error ", e , " while connect to socket")
			else:
				if Debug: print ("gs1_supersock connect_to_socket success")
				self.sock_activated=True
				return True
			time.sleep(1)
		print("gs1_supersock TimeOut connect to socket")
		return False

	def lock_reader(self):
		if Debug: print('lock_reader s')
		self.readlock.acquire()
		if Debug: print('lock_reader e')

	def release_reader(self):
		if Debug: print('release_reader s')
		self.readlock.release()
		if Debug: print('release_reader e')

	def lock_writer(self):
		if Debug: print('lock_writer s')
		self.writelock.acquire()
		if Debug: print('lock_writer e')

	def release_writer(self):
		if Debug: print('release_writer s')
		self.writelock.release()
		if Debug: print('release_writer e')

	def disconnect(self):
		if Debug: print ("gs1_supersock disconnect")
		try:
			self.sock.close()
		except socket.error as e:
			print ("Error ", e , " while disconnect from socket")


	def __init__(self):
		if Debug: print ("gs1_supersock constructor")
		self.version="solver"
		self.sock = socket.socket()
		self.sock.settimeout(1)
		self.sock.setsockopt( socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
		self.writelock = threading.Lock()
		self.readlock = threading.Lock()
		self.stoprader=False
		self.stopcallback=False
		self.mainstruct='iiiiiiii'
		data = struct.pack(self.mainstruct, 0, 0, 0, 0, 0, 0, 0, 0)
		if len(data) != 32 :
			print('Error: sizeof(int)!=4')

	def terminate(self):
		if Debug: print ("gs1_supersock destructor")
		self.stop_callback_msg()
		self.disconnect()

	def __del__(self):
		if Debug: print ("gs1_supersock destructor")
		self.terminate()


# класс программы солвера - может подключаться к запущенному солверу, к серверу, или запускать свой собственный солвер
class gs1:
	terminate_on_exit = False # Посылать команду QUIT перед отсоединением
	syncronized=False # если на сервере есть в очереди команды, то поток рассинхронизирован
	version=r"solver"


	def run_local_solver(self,path,port,version=None): # запустим солвер в указанном каталоге и подключаемся к нему
		return self.ssock.run_local_solver(path,port,version)

	def sync(self,force=False): # дожидается выполнения прежних команд, при этом выкидывает ответы от них
		if ((not self.syncronized) or force):
			self.syncronized=False
			# блокировать отправку не нужно, поскольку функцию нужно вызывать уже в заблокированной секции
			if self.ssock.send_simple(commands.SYNC):
				while True:
					msg=self.ssock.read_msg(nolock=True) # nolock=True - мы уже в критической секции, без этого флага получим deadlock
					if Debug: print("MSG:", msg)
					if msg['command'] == commands.SYNC:
						self.syncronized=True
						if Debug: print ("SYNC True")
						return True
					else:
						if(msg['command'] == commands.ERR):
							if Debug: print ("SYNC False")
							return False
						else:
							continue
			if Debug: print ("SYNC False")
			return False
		if Debug: print ("SYNC True")
		return True

	def help_send(self,syncronus=False): # просто отправляет команду help на сервер
		if not syncronus: self.syncronized=False
		return self.ssock.send_simple(commands.HELP)
	def help(self): # отправляет команду help на сервер и дожидается и принимает ответ
		self.ssock.lock_writer() # блокируем отправку команд - чтобы никто не вызвал нам чего-то ещё
		self.ssock.lock_reader() # блокмруем чтение команд - чтобы никто не перехватил наши ответы сервера (асинхронные ридеры)
		self.sync() # дожидается выполнения прежних команд, при этом выкидывает ответы от них
		if self.help_send(syncronus=True):
			while True:
				msg=self.ssock.read_msg(nolock=True) # nolock=True - мы уже в критической секции, без этого флага получим deadlock
				if Debug: print("MSG:", msg)
				if msg['command'] == commands.HELP:
					self.ssock.release_reader() #
					self.ssock.release_writer() #
					return msg['param'].decode("utf-8")[0:-1]
				else:
					if(msg['command'] == commands.ERR):
						print("Error : ERR msg:", msg)
						break
					else:
						print( "Error in HELP: wrong msg:",msg)
		self.ssock.release_reader() #
		self.ssock.release_writer() #
		return "Error can't take help"




	def stop_send(self,syncronus=False): # просто отправляет команду stop на сервер
		if not syncronus: self.syncronized=False
		return self.ssock.send_simple(commands.STOP)
	def stop(self): # отправляет команду stop на сервер, когда очередь станет пустой
		self.ssock.lock_writer() # блокируем отправку команд - чтобы никто не вызвал нам чего-то ещё
		self.ssock.lock_reader() # блокмруем чтение команд - чтобы никто не перехватил наши ответы сервера (асинхронные ридеры)
		self.sync() # дожидается выполнения прежних команд, при этом выкидывает ответы от них
		if self.stop_send(syncronus=True):
			self.syncronized=False # мы не читаем ответ сервера (можем и не успеть прочитать), поэтому поток рассинхронизируется, но после stop это неважно
			self.ssock.release_reader() #
			self.ssock.release_writer() #
			if Debug: print ("STOP True")
			return True
		self.syncronized=False
		self.ssock.release_reader() #
		self.ssock.release_writer() #
		print ("Error on Stop")
		return False


	def get_model_information_send(self,syncronus=False): # просто отправляет команду GET_MODEL_INFORMATION на сервер
		if not syncronus: self.syncronized=False
		return self.ssock.send_simple(commands.GET_MODEL_INFORMATION)
	def get_model_information(self): # отправляет команду GET_MODEL_INFORMATION на сервер и дожидается и принимает ответ
		self.ssock.lock_writer() # блокируем отправку команд - чтобы никто не вызвал нам чего-то ещё
		self.ssock.lock_reader() # блокмруем чтение команд - чтобы никто не перехватил наши ответы сервера (асинхронные ридеры)
		self.sync() # дожидается выполнения прежних команд, при этом выкидывает ответы от них
		if self.get_model_information_send(syncronus=True):
			ret={}
			while True:
				msg=self.ssock.read_msg(nolock=True) # nolock=True - мы уже в критической секции, без этого флага получим deadlock
				if Debug: print("MSG:",msg)
				if msg['command'] == commands.MODEL_INFORMATION:
					ret = eval(msg['param'].decode("utf-8")[0:-1])
				else:
					if msg['command'] == commands.GET_MODEL_INFORMATION:
						self.ssock.release_reader() #
						self.ssock.release_writer() #
						ecode=struct.unpack(self.ssock.mainstruct,msg['main'])[2]
						if ecode != 0 :
							print("Error on server while take model information: ",  ecode)
							return {'err': "Error on server while take model information", 'errcode': ecode}
						else :
							return ret
					else:
						if(msg['command'] == commands.ERR):
							print("Error : ERR msg:", msg)
							break
						else:
							print("Error : wrong msg:", msg)
		self.ssock.release_reader() #
		self.ssock.release_writer() #
		return {'err':"Error can't take model information",'errcode':-9999}


	def parallel_settings_send(self,syncronus=False,thr_per_rank=1): # просто отправляет команду PARALLEL_SETTINGS на сервер
		if not syncronus: self.syncronized=False
		return self.ssock.send_dict(commands.PARALLEL_SETTINGS,{'thr_per_rank':int(thr_per_rank)})
	def parallel_settings(self,thr_per_rank=1): # отправляет команду PARALLEL_SETTINGS на сервер и дожидается и принимает ответ
		self.ssock.lock_writer() # блокируем отправку команд - чтобы никто не вызвал нам чего-то ещё
		self.ssock.lock_reader() # блокмруем чтение команд - чтобы никто не перехватил наши ответы сервера (асинхронные ридеры)
		self.sync() # дожидается выполнения прежних команд, при этом выкидывает ответы от них
		if self.parallel_settings_send(syncronus=True,thr_per_rank=thr_per_rank):
			ret={}
			while True:
				msg=self.ssock.read_msg(nolock=True) # nolock=True - мы уже в критической секции, без этого флага получим deadlock
				if Debug: print("MSG:",msg)
				if msg['command'] == commands.PARALLEL_SETTINGS:
					self.ssock.release_reader() #
					self.ssock.release_writer() #
					mdata=struct.unpack(self.ssock.mainstruct,msg['main'])
					ecode=mdata[2]
					thrret=mdata[3]
					if ecode != 0 :
						print("Error on server while set parallel settings: ",  ecode)
						return {'err':"Error on server while set parallel settings:",'errcode':ecode}
					else :
						return {"thr_per_rank":thrret}
				else:
					if (msg['command'] == commands.ERR):
						print("Error : ERR msg:", msg)
						break
					else:
						print("Error while set parallel settings: unexpected MSG:", msg)

		self.ssock.release_reader() #
		self.ssock.release_writer() #
		return {'err':"Error on server while set parallel settings:",'errcode':-9999}

	def get_solver_information_send(self,solver=None,syncronus=False): # отправляет команду GET_SOLVER_INFORMATION c параметрами на сервер
		if not syncronus: self.syncronized=False
		if solver is None:
			return self.ssock.send_simple(commands.GET_SOLVER_INFORMATION)
		else:
			return self.ssock.send_dict(commands.GET_SOLVER_INFORMATION,{'solver':str(solver)})
	def get_solver_information(self,solver=None): # отправляет команду GET_SOLVER_INFORMATION на сервер и дожидается и принимает ответ
		self.ssock.lock_writer() # блокируем отправку команд - чтобы никто не вызвал нам чего-то ещё
		self.ssock.lock_reader() # блокмруем чтение команд - чтобы никто не перехватил наши ответы сервера (асинхронные ридеры)
		self.sync() # дожидается выполнения прежних команд, при этом выкидывает ответы от них
		if self.get_solver_information_send(solver=solver,syncronus=True):
			ret={}
			while True:
				msg=self.ssock.read_msg(nolock=True) # nolock=True - мы уже в критической секции, без этого флага получим deadlock
				if Debug: print("MSG:",msg)
				if msg['command'] == commands.SOLVER_INFORMATION:
					ret = eval(msg['param'].decode("utf-8")[0:-1])
				else:
					if msg['command'] == commands.GET_SOLVER_INFORMATION:
						self.ssock.release_reader() #
						self.ssock.release_writer() #
						ecode=struct.unpack(self.ssock.mainstruct,msg['main'])[2]
						if ecode != 0 :
							print("Error on server while take solver information: ",  ecode)
							return {'err': "Error on server while take solver information", 'errcode': ecode}
						else :
							return ret
					else:
						if (msg['command'] == commands.ERR):
							print("Error : ERR msg:", msg)
							break
						else:
							print("Error : unexpected MSG:", msg)
		self.ssock.release_reader() #
		self.ssock.release_writer() #
		return {'err':"Error can't take solver information",'errcode':-9999}


	def fs_ls_send(self,path=None,syncronus=False): # отправляет команду FS_LS c параметрами на сервер
		if not syncronus: self.syncronized=False
		if path is None:
			return self.ssock.send_simple(commands.FS_LS)
		else:
			return self.ssock.send_dict(commands.FS_LS,{'path':str(path)})
	def fs_ls(self,path=None): # отправляет команду FS_LS на сервер и дожидается и принимает ответ
		self.ssock.lock_writer() # блокируем отправку команд - чтобы никто не вызвал нам чего-то ещё
		self.ssock.lock_reader() # блокмруем чтение команд - чтобы никто не перехватил наши ответы сервера (асинхронные ридеры)
		self.sync() # дожидается выполнения прежних команд, при этом выкидывает ответы от них
		if self.fs_ls_send(path=path,syncronus=True):
			ret={}
			while True:
				msg=self.ssock.read_msg(nolock=True) # nolock=True - мы уже в критической секции, без этого флага получим deadlock
				if Debug: print("MSG:",msg)
				if msg['command'] == commands.FS_LS_MSG:
					ret = eval(msg['param'].decode("utf-8")[0:-1])
				else:
					if msg['command'] == commands.FS_LS:
						self.ssock.release_reader() #
						self.ssock.release_writer() #
						ecode=struct.unpack(self.ssock.mainstruct,msg['main'])[2]
						if ecode != 0 :
							print("Error on server while fs ls: ",  ecode)
							return {'err': "Error on server while fs ls", 'errcode': ecode}
						else :
							return ret
					else:
						if (msg['command'] == commands.ERR):
							print("Error : ERR msg:", msg)
							break
						else:
							print("Error : unexpected MSG:", msg)
		self.ssock.release_reader() #
		self.ssock.release_writer() #
		return {'err':"Error can't take fs ls",'errcode':-9999}


	def fs_mkdir_send(self,path=None,syncronus=False): # отправляет команду FS_MKDIR c параметрами на сервер
		if not syncronus: self.syncronized=False
		if path is None:
			print("Error on server while fs mkdir: ",  -9998)
			return False
		else:
			return self.ssock.send_dict(commands.FS_MKDIR,{'path':str(path)})
	def fs_mkdir(self,path=None): # отправляет команду FS_MKDIR на сервер и дожидается и принимает ответ
		self.ssock.lock_writer() # блокируем отправку команд - чтобы никто не вызвал нам чего-то ещё
		self.ssock.lock_reader() # блокмруем чтение команд - чтобы никто не перехватил наши ответы сервера (асинхронные ридеры)
		self.sync() # дожидается выполнения прежних команд, при этом выкидывает ответы от них
		if self.fs_mkdir_send(path=path,syncronus=True):
			ret={}
			while True:
				msg=self.ssock.read_msg(nolock=True) # nolock=True - мы уже в критической секции, без этого флага получим deadlock
				if Debug: print("MSG:",msg)
				if msg['command'] == commands.FS_MKDIR_MSG:
					ret = eval(msg['param'].decode("utf-8")[0:-1])
				else:
					if msg['command'] == commands.FS_MKDIR:
						self.ssock.release_reader() #
						self.ssock.release_writer() #
						ecode=struct.unpack(self.ssock.mainstruct,msg['main'])[2]
						if ecode != 0 :
							print("Error on server while fs mkdir: ",  ecode)
							return {'err': "Error on server while fs mkdir", 'errcode': ecode}
						else :
							return ret
					else:
						if (msg['command'] == commands.ERR):
							print("Error : ERR msg:", msg)
							break
						else:
							print("Error : unexpected MSG:", msg)
		self.ssock.release_reader() #
		self.ssock.release_writer() #
		return {'err':"Error can't take fs mkdir",'errcode':-9999}

	def fs_copy_send(self,From=None,To=None,syncronus=False): # отправляет команду FS_COPY c параметрами на сервер
		if not syncronus: self.syncronized=False
		if (From is None)or(To is None):
			print("Error on server while fs copy: ",  -9998)
			return False
		else:
			return self.ssock.send_dict(commands.FS_COPY,{'from':str(From),'to':str(To)})
	def fs_copy(self,From=None,To=None): # отправляет команду FS_COPY на сервер и дожидается и принимает ответ
		self.ssock.lock_writer() # блокируем отправку команд - чтобы никто не вызвал нам чего-то ещё
		self.ssock.lock_reader() # блокмруем чтение команд - чтобы никто не перехватил наши ответы сервера (асинхронные ридеры)
		self.sync() # дожидается выполнения прежних команд, при этом выкидывает ответы от них
		if self.fs_copy_send(From=From,To=To,syncronus=True):
			ret={}
			while True:
				msg=self.ssock.read_msg(nolock=True) # nolock=True - мы уже в критической секции, без этого флага получим deadlock
				if Debug: print("MSG:",msg)
				if msg['command'] == commands.FS_COPY_MSG:
					ret = eval(msg['param'].decode("utf-8")[0:-1])
				else:
					if msg['command'] == commands.FS_COPY:
						self.ssock.release_reader() #
						self.ssock.release_writer() #
						ecode=struct.unpack(self.ssock.mainstruct,msg['main'])[2]
						if ecode != 0 :
							print("Error on server while fs copy: ",  ecode)
							return {'err': "Error on server while fs copy", 'errcode': ecode}
						else :
							return ret
					else:
						if (msg['command'] == commands.ERR):
							print("Error : ERR msg:", msg)
							break
						else:
							print("Error : unexpected MSG:", msg)
		self.ssock.release_reader() #
		self.ssock.release_writer() #
		return {'err':"Error can't take fs copy",'errcode':-9999}

	def fs_rm_send(self,path=None,syncronus=False): # отправляет команду FS_RM c параметрами на сервер
		if not syncronus: self.syncronized=False
		if path is None:
			print("Error on server while fs rm: ",  -9998)
			return False
		else:
			return self.ssock.send_dict(commands.FS_RM,{'path':str(path)})
	def fs_rm(self,path=None): # отправляет команду FS_RM на сервер и дожидается и принимает ответ
		self.ssock.lock_writer() # блокируем отправку команд - чтобы никто не вызвал нам чего-то ещё
		self.ssock.lock_reader() # блокмруем чтение команд - чтобы никто не перехватил наши ответы сервера (асинхронные ридеры)
		self.sync() # дожидается выполнения прежних команд, при этом выкидывает ответы от них
		if self.fs_rm_send(path=path,syncronus=True):
			ret={}
			while True:
				msg=self.ssock.read_msg(nolock=True) # nolock=True - мы уже в критической секции, без этого флага получим deadlock
				if Debug: print("MSG:",msg)
				if msg['command'] == commands.FS_RM_MSG:
					ret = eval(msg['param'].decode("utf-8")[0:-1])
				else:
					if msg['command'] == commands.FS_RM:
						self.ssock.release_reader() #
						self.ssock.release_writer() #
						ecode=struct.unpack(self.ssock.mainstruct,msg['main'])[2]
						if ecode != 0 :
							print("Error on server while fs rm: ",  ecode)
							return {'err': "Error on server while fs rm", 'errcode': ecode}
						else :
							return ret
					else:
						if (msg['command'] == commands.ERR):
							print("Error : ERR msg:", msg)
							break
						else:
							print("Error : unexpected MSG:", msg)
		self.ssock.release_reader() #
		self.ssock.release_writer() #
		return {'err':"Error can't take fs rm",'errcode':-9999}

	def fs_move_send(self,From=None,To=None,syncronus=False): # отправляет команду FS_MOVE c параметрами на сервер
		if not syncronus: self.syncronized=False
		if (From is None)or(To is None):
			print("Error on server while fs move: ",  -9998)
			return False
		else:
			return self.ssock.send_dict(commands.FS_MOVE,{'from':str(From),'to':str(To)})
	def fs_move(self,From=None,To=None): # отправляет команду FS_MOVE на сервер и дожидается и принимает ответ
		self.ssock.lock_writer() # блокируем отправку команд - чтобы никто не вызвал нам чего-то ещё
		self.ssock.lock_reader() # блокмруем чтение команд - чтобы никто не перехватил наши ответы сервера (асинхронные ридеры)
		self.sync() # дожидается выполнения прежних команд, при этом выкидывает ответы от них
		if self.fs_move_send(From=From,To=To,syncronus=True):
			ret={}
			while True:
				msg=self.ssock.read_msg(nolock=True) # nolock=True - мы уже в критической секции, без этого флага получим deadlock
				if Debug: print("MSG:",msg)
				if msg['command'] == commands.FS_MOVE_MSG:
					ret = eval(msg['param'].decode("utf-8")[0:-1])
				else:
					if msg['command'] == commands.FS_MOVE:
						self.ssock.release_reader() #
						self.ssock.release_writer() #
						ecode=struct.unpack(self.ssock.mainstruct,msg['main'])[2]
						if ecode != 0 :
							print("Error on server while fs move: ",  ecode)
							return {'err': "Error on server while fs move", 'errcode': ecode}
						else :
							return ret
					else:
						if (msg['command'] == commands.ERR):
							print("Error : ERR msg:", msg)
							break
						else:
							print("Error : unexpected MSG:", msg)
		self.ssock.release_reader() #
		self.ssock.release_writer() #
		return {'err':"Error can't take fs move",'errcode':-9999}

	def write_info_send(self,gs1_path=None,syncronus=False): # отправляет команду WRITE_INFO c параметрами на сервер
		if not syncronus: self.syncronized=False
		if gs1_path is None:
			return False
		else:
			return self.ssock.send_dict(commands.WRITE_INFO,{'gs1_path':str(gs1_path)})
	def write_info(self,gs1_path=None): # отправляет команду WRITE_INFO на сервер и дожидается и принимает ответ
		self.ssock.lock_writer() # блокируем отправку команд - чтобы никто не вызвал нам чего-то ещё
		self.ssock.lock_reader() # блокмруем чтение команд - чтобы никто не перехватил наши ответы сервера (асинхронные ридеры)
		self.sync() # дожидается выполнения прежних команд, при этом выкидывает ответы от них
		if self.write_info_send(gs1_path=gs1_path,syncronus=True):
			while True:
				msg=self.ssock.read_msg(nolock=True) # nolock=True - мы уже в критической секции, без этого флага получим deadlock
				if Debug: print("MSG:", msg)
				if msg['command'] == commands.WRITE_INFO:
					self.ssock.release_reader() #
					self.ssock.release_writer() #
					ecode=struct.unpack(self.ssock.mainstruct,msg['main'])[2]
					if ecode != 0 :
						print("Error on server while write_info: ",  ecode)
						return False
					else :
						return True

				else:
					if (msg['command'] == commands.ERR):
						print("Error : ERR msg:", msg)
						break
					else:
						print("Error : unexpected MSG:", msg)
		self.ssock.release_reader() #
		self.ssock.release_writer() #
		print("Error: can't take write_info")
		return False


	def distribute_send(self,syncronus=False): # отправляет команду WRITE_INFO c параметрами на сервер
		if not syncronus: self.syncronized=False
		return self.ssock.send_simple(commands.DISTRIBUTE)
	def distribute(self): # отправляет команду WRITE_INFO на сервер и дожидается и принимает ответ
		self.ssock.lock_writer() # блокируем отправку команд - чтобы никто не вызвал нам чего-то ещё
		self.ssock.lock_reader() # блокмруем чтение команд - чтобы никто не перехватил наши ответы сервера (асинхронные ридеры)
		self.sync() # дожидается выполнения прежних команд, при этом выкидывает ответы от них
		if self.distribute_send(syncronus=True):
			while True:
				msg=self.ssock.read_msg(nolock=True) # nolock=True - мы уже в критической секции, без этого флага получим deadlock
				if Debug: print("MSG:", msg)
				if msg['command'] == commands.DISTRIBUTE:
					self.ssock.release_reader() #
					self.ssock.release_writer() #
					ecode=struct.unpack(self.ssock.mainstruct,msg['main'])[2]
					if ecode != 0 :
						print("Error on server while distribute: ",  ecode)
						return False
					else :
						return True
				else:
					if (msg['command'] == commands.ERR):
						print("Error : ERR msg:", msg)
						break
					else:
						print("Error : unexpected MSG:", msg)
		self.ssock.release_reader() #
		self.ssock.release_writer() #
		print("Error: can't take distribute")
		return False

	def get_probes_send(self,syncronus=False): # отправляет команду GET_PROBES c параметрами на сервер
		if not syncronus: self.syncronized=False
		return self.ssock.send_simple(commands.GET_PROBES)
	def get_probes(self): # отправляет команду GET_PROBES на сервер и дожидается и принимает ответ
		self.ssock.lock_writer() # блокируем отправку команд - чтобы никто не вызвал нам чего-то ещё
		self.ssock.lock_reader() # блокмруем чтение команд - чтобы никто не перехватил наши ответы сервера (асинхронные ридеры)
		self.sync() # дожидается выполнения прежних команд, при этом выкидывает ответы от них
		if self.get_probes_send(syncronus=True):
			ret={}
			while True:
				msg=self.ssock.read_msg(nolock=True) # nolock=True - мы уже в критической секции, без этого флага получим deadlock
				if Debug: print("MSG:",msg)
				if msg['command'] == commands.PROBE_INFO:
					ret = eval(msg['param'].decode("utf-8")[0:-1])
				else:
					if msg['command'] == commands.GET_PROBES:
						self.ssock.release_reader() #
						self.ssock.release_writer() #
						ecode=struct.unpack(self.ssock.mainstruct,msg['main'])[2]
						if ecode != 0 :
							print("Error on server while take probes: ",  ecode)
							return {'err': "Error on server while take probes", 'errcode': ecode}
						else :
							return ret
					else:
						if (msg['command'] == commands.ERR):
							print("Error : ERR msg:", msg)
							break
						else:
							print("Error : unexpected MSG:", msg)
		self.ssock.release_reader() #
		self.ssock.release_writer() #
		return {'err':"Error can't take probes",'errcode':-9999}


	def get_probes_integrals_send(self,syncronus=False): # отправляет команду GET_PROBES_INTEGRALS c параметрами на сервер
		if not syncronus: self.syncronized=False
		return self.ssock.send_simple(commands.GET_PROBES_INTEGRALS)
	def get_probes_integrals(self): # отправляет команду GET_PROBES_INTEGRALS на сервер и дожидается и принимает ответ
		self.ssock.lock_writer() # блокируем отправку команд - чтобы никто не вызвал нам чего-то ещё
		self.ssock.lock_reader() # блокмруем чтение команд - чтобы никто не перехватил наши ответы сервера (асинхронные ридеры)
		self.sync() # дожидается выполнения прежних команд, при этом выкидывает ответы от них
		if self.get_probes_integrals_send(syncronus=True):
			ret={}
			while True:
				msg=self.ssock.read_msg(nolock=True) # nolock=True - мы уже в критической секции, без этого флага получим deadlock
				if Debug: print("MSG:",msg)
				if msg['command'] == commands.PROBE_INTEGRALS:
					ret = eval(msg['param'].decode("utf-8")[0:-1])
				else:
					if msg['command'] == commands.GET_PROBES_INTEGRALS:
						self.ssock.release_reader() #
						self.ssock.release_writer() #
						ecode=struct.unpack(self.ssock.mainstruct,msg['main'])[2]
						if ecode != 0 :
							print("Error on server while take probes_integrals: ",  ecode)
							return {'err': "Error on server while take probes_integrals", 'errcode': ecode}
						else :
							return ret
					else:
						if (msg['command'] == commands.ERR):
							print("Error : ERR msg:", msg)
							break
						else:
							print("Error : unexpected MSG:", msg)
		self.ssock.release_reader() #
		self.ssock.release_writer() #
		return {'err':"Error can't take probes_integrals",'errcode':-9999}




	def export_send(self,files,type=None,write_static=None,write_dynamic=None,zone_filter=None, boundary_filter=None,export_fictive=False,syncronus=False): # отправляет команду EXPORT c параметрами на сервер
		if not syncronus: self.syncronized=False
		if (not isinstance(files, list)):
			return False
		else:
			dc={"files":files,"export_fictive":bool(export_fictive)}
			if not (write_static is None):
				dc['write_static']=bool(write_static)
			if not (write_dynamic is None):
				dc['write_dynamic']=bool(write_dynamic)
			if not (type is None):
				dc['type']=str(type)
			if not (zone_filter is None):
				dc['zone_filter']=str(zone_filter)
			if not (boundary_filter is None):
				dc['boundary_filter']=str(boundary_filter)
			return self.ssock.send_dict(commands.EXPORT,dc)




	def export(self,files,type=None,write_static=None,write_dynamic=None,zone_filter=None, boundary_filter=None,export_fictive=False): # отправляет команду EXPORT_PLOT3D_STATIC на сервер и дожидается и принимает ответ
		self.ssock.lock_writer() # блокируем отправку команд - чтобы никто не вызвал нам чего-то ещё
		self.ssock.lock_reader() # блокмруем чтение команд - чтобы никто не перехватил наши ответы сервера (асинхронные ридеры)
		self.sync() # дожидается выполнения прежних команд, при этом выкидывает ответы от них
		if self.export_send(files=files,type=type,write_static=write_static,write_dynamic=write_dynamic,zone_filter=zone_filter,boundary_filter=boundary_filter,export_fictive=export_fictive,syncronus=True):
			while True:
				msg=self.ssock.read_msg(nolock=True) # nolock=True - мы уже в критической секции, без этого флага получим deadlock
				if Debug: print("MSG:", msg)
				if msg['command'] == commands.EXPORT:
					self.ssock.release_reader() #
					self.ssock.release_writer() #
					ecode=struct.unpack(self.ssock.mainstruct,msg['main'])[2]
					if ecode != 0 :
						print("Error on server while export: ",  ecode)
						return False
					else :
						return True

				else:
					if (msg['command'] == commands.ERR):
						print("Error : ERR msg:", msg)
						break
					else:
						print("Error : unexpected MSG:", msg)
		self.ssock.release_reader() #
		self.ssock.release_writer() #
		print("Error: can't take export")
		return False

	def export_static(self,files,type=None): # отправляет команду EXPORT_STATIC на сервер и дожидается и принимает ответ
		return self.export(files=files,type=type,write_static=True,write_dynamic=False);


	def export_dynamic(self,files,type=None): # отправляет команду EXPORT_DYNAMIC на сервер и дожидается и принимает ответ
		return self.export(files=files,type=type,write_static=False,write_dynamic=True);


	def import_mesh_send(self,files,type=None,solver=None,syncronus=False): # отправляет команду IMPORT c параметрами на сервер
		if not syncronus: self.syncronized=False
		if (not isinstance(files, list)):
			return False
		else:
			dc={"files":files}
			if not (solver is None):
				dc['solver']=str(solver)
			if not (type is None):
				dc['type']=str(type)
			return self.ssock.send_dict(commands.IMPORT,dc)
	def import_mesh(self,files,type=None,solver=None): # отправляет команду IMPORT на сервер и дожидается и принимает ответ
		self.ssock.lock_writer() # блокируем отправку команд - чтобы никто не вызвал нам чего-то ещё
		self.ssock.lock_reader() # блокмруем чтение команд - чтобы никто не перехватил наши ответы сервера (асинхронные ридеры)
		self.sync() # дожидается выполнения прежних команд, при этом выкидывает ответы от них
		if self.import_mesh_send(files=files,type=type,solver=solver,syncronus=True):
			while True:
				msg=self.ssock.read_msg(nolock=True) # nolock=True - мы уже в критической секции, без этого флага получим deadlock
				if Debug: print("MSG:", msg)
				if msg['command'] == commands.IMPORT:
					self.ssock.release_reader() #
					self.ssock.release_writer() #
					ecode=struct.unpack(self.ssock.mainstruct,msg['main'])[2]
					if ecode != 0 :
						print("Error on server while import: ",  ecode)
						return False
					else :
						return True

				else:
					if (msg['command'] == commands.ERR):
						print("Error : ERR msg:", msg)
						break
					else:
						print("Error : unexpected MSG:", msg)
		self.ssock.release_reader() #
		self.ssock.release_writer() #
		print("Error: can't take import")
		return False

	def calc_iteration_send(self,syncronus=False): # отправляет команду CALC_ITERATION c параметрами на сервер
		if not syncronus: self.syncronized=False
		return self.ssock.send_simple(commands.CALC_ITERATION)
	def calc_iteration(self): # отправляет команду CALC_ITERATION на сервер и дожидается и принимает ответ
		self.ssock.lock_writer() # блокируем отправку команд - чтобы никто не вызвал нам чего-то ещё
		self.ssock.lock_reader() # блокмруем чтение команд - чтобы никто не перехватил наши ответы сервера (асинхронные ридеры)
		self.sync() # дожидается выполнения прежних команд, при этом выкидывает ответы от них
		if self.calc_iteration_send(syncronus=True):
			while True:
				msg=self.ssock.read_msg(nolock=True) # nolock=True - мы уже в критической секции, без этого флага получим deadlock
				if Debug: print("MSG:", msg)
				if msg['command'] == commands.CALC_ITERATION:
					self.ssock.release_reader() #
					self.ssock.release_writer() #
					idata=struct.unpack(self.ssock.mainstruct,msg['main'])
					ecode=idata[2]
					calc_converged=idata[3]
					if ecode != 0 :
						print("Error on server while calc_iteration: ",  ecode)
						return {'err':"Error can't take calc_iteration",'errcode':ecode,"converged":calc_converged}
					else :
						return {"converged":calc_converged}
				else:
					if (msg['command'] == commands.ERR):
						print("Error : ERR msg:", msg)
						break
					else:
						print("Error : unexpected MSG:", msg)
		self.ssock.release_reader() #
		self.ssock.release_writer() #
		return {'err':"Error can't take calc_iteration",'errcode':-9999}


	def calc_iterate_send(self,iterations_count=None,gs1_path=None,gs1_save_interval=None,export_path=None,export_type=None,export_fictive=False,export_save_interval=None,syncronus=False): # отправляет команду CALC_ITERATE c параметрами на сервер
		if not syncronus: self.syncronized=False
		ds={"export_fictive":bool(export_fictive)}
		if not(iterations_count is None): ds['iterations_count']=iterations_count
		if not(gs1_path is None): ds['gs1_path']=gs1_path
		if not(gs1_save_interval is None): ds['gs1_save_interval']=gs1_save_interval
		if not(export_path is None): ds['export_path']=export_path
		if not(export_type is None): ds['export_type']=export_type
		if not(export_save_interval is None): ds['export_save_interval']=export_save_interval
		return self.ssock.send_dict(commands.CALC_ITERATE,ds)
	def calc_iterate(self,iterations_count=None,gs1_path=None,gs1_save_interval=None,export_path=None,export_type=None,export_fictive=False,export_save_interval=None): # отправляет команду CALC_ITERATE на сервер и дожидается и принимает ответ
		self.ssock.lock_writer() # блокируем отправку команд - чтобы никто не вызвал нам чего-то ещё
		self.ssock.lock_reader() # блокмруем чтение команд - чтобы никто не перехватил наши ответы сервера (асинхронные ридеры)
		self.sync() # дожидается выполнения прежних команд, при этом выкидывает ответы от них
		if self.calc_iterate_send(iterations_count=iterations_count,gs1_path=gs1_path,gs1_save_interval=gs1_save_interval,export_path=export_path,export_type=export_type,export_fictive=export_fictive,export_save_interval=export_save_interval,syncronus=True):
			while True:
				msg=self.ssock.read_msg(nolock=True) # nolock=True - мы уже в критической секции, без этого флага получим deadlock
				if Debug: print("MSG:",msg)
				if msg['command'] == commands.COMMAND_QUEUE_PROGRESS:
					mdata=struct.unpack('iiiifiii',msg['main'])
					print("Progress of calc_iterate :",  mdata[4],"%")
				else:
					if msg['command'] == commands.CALC_ITERATE:
						self.ssock.release_reader() #
						self.ssock.release_writer() #
						mdata=struct.unpack(self.ssock.mainstruct,msg['main'])
						ecode=mdata[2]
						rcode=mdata[3]
						if ecode != 0 :
							print("Error on server while calc_iterate: ",  ecode)
							return {'err': "Error on server while calc_iterate", 'errcode': ecode,"converged":rcode}
						else :
							return {"converged":rcode}
					else:
						if (msg['command'] == commands.ERR):
							print("Error : ERR msg:", msg)
							break
						else:
							ccode=struct.unpack(self.ssock.mainstruct,msg['main'])[2]
							print("Take ",commands(ccode).name," : ", msg)
		self.ssock.release_reader() #
		self.ssock.release_writer() #
		return {'err':"Error can't take calc_iterate",'errcode':-9999}


	def read_dynamic_send(self,gs1_path=None,iteration_number=None,syncronus=False): # отправляет команду READ_DYNAMIC c параметрами на сервер
		if not syncronus: self.syncronized=False
		if (gs1_path is None):
			return False
		else:
			dc={'gs1_path':str(gs1_path)}
			if not (iteration_number is None):
				dc['iteration_number']=int(iteration_number)
			return self.ssock.send_dict(commands.READ_DYNAMIC,dc)
	def read_dynamic(self,gs1_path=None,iteration_number=None): # отправляет команду READ_DYNAMIC на сервер и дожидается и принимает ответ
		self.ssock.lock_writer() # блокируем отправку команд - чтобы никто не вызвал нам чего-то ещё
		self.ssock.lock_reader() # блокмруем чтение команд - чтобы никто не перехватил наши ответы сервера (асинхронные ридеры)
		self.sync() # дожидается выполнения прежних команд, при этом выкидывает ответы от них
		if self.read_dynamic_send(gs1_path=gs1_path,iteration_number=iteration_number,syncronus=True):
			while True:
				msg=self.ssock.read_msg(nolock=True) # nolock=True - мы уже в критической секции, без этого флага получим deadlock
				if Debug: print("MSG:", msg)
				if msg['command'] == commands.READ_DYNAMIC:
					self.ssock.release_reader() #
					self.ssock.release_writer() #
					ecode=struct.unpack(self.ssock.mainstruct,msg['main'])[2]
					if ecode != 0 :
						print("Error on server while read_dynamic: ",  ecode)
						return False
					else :
						return True
				else:
					if (msg['command'] == commands.ERR):
						print("Error : ERR msg:", msg)
						break
					else:
						print("Error : unexpected MSG:", msg)
		self.ssock.release_reader() #
		self.ssock.release_writer() #
		print("Error: can't take read_dynamic")
		return False


	def read_static_send(self,gs1_path=None,syncronus=False): # отправляет команду READ_STATIC c параметрами на сервер
		if not syncronus: self.syncronized=False
		if (gs1_path is None):
			return False
		else:
			dc={'gs1_path':str(gs1_path)}
			return self.ssock.send_dict(commands.READ_STATIC,dc)
	def read_static(self,gs1_path=None): # отправляет команду READ_STATIC на сервер и дожидается и принимает ответ
		self.ssock.lock_writer() # блокируем отправку команд - чтобы никто не вызвал нам чего-то ещё
		self.ssock.lock_reader() # блокмруем чтение команд - чтобы никто не перехватил наши ответы сервера (асинхронные ридеры)
		self.sync() # дожидается выполнения прежних команд, при этом выкидывает ответы от них
		if self.read_static_send(gs1_path=gs1_path,syncronus=True):
			while True:
				msg=self.ssock.read_msg(nolock=True) # nolock=True - мы уже в критической секции, без этого флага получим deadlock
				if Debug: print("MSG:", msg)
				if msg['command'] == commands.READ_STATIC:
					self.ssock.release_reader() #
					self.ssock.release_writer() #
					ecode=struct.unpack(self.ssock.mainstruct,msg['main'])[2]
					if ecode != 0 :
						print("Error on server while read_static: ",  ecode)
						return False
					else :
						return True
				else:
					if (msg['command'] == commands.ERR):
						print("Error : ERR msg:", msg)
						break
					else:
						print("Error : unexpected MSG:", msg)
		self.ssock.release_reader() #
		self.ssock.release_writer() #
		print("Error: can't take read_static")
		return False


	def set_timestep_send(self,timestep=None,syncronus=False): # отправляет команду SET_TIMESTEP c параметрами на сервер
		if not syncronus: self.syncronized=False
		if (timestep is None):
			return False
		else:
			dc={'timestep':int(timestep)}
			return self.ssock.send_dict(commands.SET_TIMESTEP,dc)
	def set_timestep(self,timestep=None): # отправляет команду SET_TIMESTEP на сервер и дожидается и принимает ответ
		self.ssock.lock_writer() # блокируем отправку команд - чтобы никто не вызвал нам чего-то ещё
		self.ssock.lock_reader() # блокмруем чтение команд - чтобы никто не перехватил наши ответы сервера (асинхронные ридеры)
		self.sync() # дожидается выполнения прежних команд, при этом выкидывает ответы от них
		if self.set_timestep_send(timestep=timestep,syncronus=True):
			while True:
				msg=self.ssock.read_msg(nolock=True) # nolock=True - мы уже в критической секции, без этого флага получим deadlock
				if Debug: print("MSG:", msg)
				if msg['command'] == commands.SET_TIMESTEP:
					self.ssock.release_reader() #
					self.ssock.release_writer() #
					ecode=struct.unpack(self.ssock.mainstruct,msg['main'])[2]
					if ecode != 0 :
						print("Error on server while set_timestep: ",  ecode)
						return False
					else :
						return True
				else:
					if (msg['command'] == commands.ERR):
						print("Error : ERR msg:", msg)
						break
					else:
						print("Error : unexpected MSG:", msg)
		self.ssock.release_reader() #
		self.ssock.release_writer() #
		print("Error: can't take set_timestep")
		return False


	def set_dt_send(self,dt=None,syncronus=False): # отправляет команду SET_DT c параметрами на сервер
		if not syncronus: self.syncronized=False
		if (dt is None):
			return False
		else:
			dc={'dt':float(dt)}
			return self.ssock.send_dict(commands.SET_DT,dc)
	def set_dt(self,dt=None): # отправляет команду SET_DT на сервер и дожидается и принимает ответ
		self.ssock.lock_writer() # блокируем отправку команд - чтобы никто не вызвал нам чего-то ещё
		self.ssock.lock_reader() # блокмруем чтение команд - чтобы никто не перехватил наши ответы сервера (асинхронные ридеры)
		self.sync() # дожидается выполнения прежних команд, при этом выкидывает ответы от них
		if self.set_dt_send(dt=dt,syncronus=True):
			while True:
				msg=self.ssock.read_msg(nolock=True) # nolock=True - мы уже в критической секции, без этого флага получим deadlock
				if Debug: print("MSG:", msg)
				if msg['command'] == commands.SET_DT:
					self.ssock.release_reader() #
					self.ssock.release_writer() #
					ecode=struct.unpack(self.ssock.mainstruct,msg['main'])[2]
					if ecode != 0 :
						print("Error on server while set_dt: ",  ecode)
						return False
					else :
						return True
				else:
					if (msg['command'] == commands.ERR):
						print("Error : ERR msg:", msg)
						break
					else:
						print("Error : unexpected MSG:", msg)
		self.ssock.release_reader() #
		self.ssock.release_writer() #
		print("Error: can't take set_dt")
		return False


	def set_time_send(self,time=None,syncronus=False): # отправляет команду SET_TIME c параметрами на сервер
		if not syncronus: self.syncronized=False
		if (time is None):
			return False
		else:
			dc={'time':float(time)}
			return self.ssock.send_dict(commands.SET_TIME,dc)
	def set_time(self,time=None): # отправляет команду SET_TIME на сервер и дожидается и принимает ответ
		self.ssock.lock_writer() # блокируем отправку команд - чтобы никто не вызвал нам чего-то ещё
		self.ssock.lock_reader() # блокмруем чтение команд - чтобы никто не перехватил наши ответы сервера (асинхронные ридеры)
		self.sync() # дожидается выполнения прежних команд, при этом выкидывает ответы от них
		if self.set_time_send(time=time,syncronus=True):
			while True:
				msg=self.ssock.read_msg(nolock=True) # nolock=True - мы уже в критической секции, без этого флага получим deadlock
				if Debug: print("MSG:", msg)
				if msg['command'] == commands.SET_TIME:
					self.ssock.release_reader() #
					self.ssock.release_writer() #
					ecode=struct.unpack(self.ssock.mainstruct,msg['main'])[2]
					if ecode != 0 :
						print("Error on server while set_time: ",  ecode)
						return False
					else :
						return True
				else:
					if (msg['command'] == commands.ERR):
						print("Error : ERR msg:", msg)
						break
					else:
						print("Error : unexpected MSG:", msg)
		self.ssock.release_reader() #
		self.ssock.release_writer() #
		print("Error: can't take set_time")
		return False

	def init_dynamic_send(self,syncronus=False): # отправляет команду INIT_DYNAMIC c параметрами на сервер
		if not syncronus: self.syncronized=False
		return self.ssock.send_simple(commands.INIT_DYNAMIC)
	def init_dynamic(self): # отправляет команду INIT_DYNAMIC на сервер и дожидается и принимает ответ
		self.ssock.lock_writer() # блокируем отправку команд - чтобы никто не вызвал нам чего-то ещё
		self.ssock.lock_reader() # блокмруем чтение команд - чтобы никто не перехватил наши ответы сервера (асинхронные ридеры)
		self.sync() # дожидается выполнения прежних команд, при этом выкидывает ответы от них
		if self.init_dynamic_send(syncronus=True):
			while True:
				msg=self.ssock.read_msg(nolock=True) # nolock=True - мы уже в критической секции, без этого флага получим deadlock
				if Debug: print("MSG:", msg)
				if msg['command'] == commands.INIT_DYNAMIC:
					self.ssock.release_reader() #
					self.ssock.release_writer() #
					ecode=struct.unpack(self.ssock.mainstruct,msg['main'])[2]
					if ecode != 0 :
						print("Error on server while init_dynamic: ",  ecode)
						return False
					else :
						return True
				else:
					if (msg['command'] == commands.ERR):
						print("Error : ERR msg:", msg)
						break
					else:
						print("Error : unexpected MSG:", msg)
		self.ssock.release_reader() #
		self.ssock.release_writer() #
		print("Error: can't take init_dynamic")
		return False

#######################################################################################################################





	def init_static_send(self,syncronus=False): # отправляет команду INIT_STATIC c параметрами на сервер
		if not syncronus: self.syncronized=False
		return self.ssock.send_simple(commands.INIT_STATIC)
	def init_static(self): # отправляет команду INIT_STATIC на сервер и дожидается и принимает ответ
		self.ssock.lock_writer() # блокируем отправку команд - чтобы никто не вызвал нам чего-то ещё
		self.ssock.lock_reader() # блокмруем чтение команд - чтобы никто не перехватил наши ответы сервера (асинхронные ридеры)
		self.sync() # дожидается выполнения прежних команд, при этом выкидывает ответы от них
		if self.init_static_send(syncronus=True):
			while True:
				msg=self.ssock.read_msg(nolock=True) # nolock=True - мы уже в критической секции, без этого флага получим deadlock
				if Debug: print("MSG:", msg)
				if msg['command'] == commands.INIT_STATIC:
					self.ssock.release_reader() #
					self.ssock.release_writer() #
					ecode=struct.unpack(self.ssock.mainstruct,msg['main'])[2]
					if ecode != 0 :
						print("Error on server while init_static: ",  ecode)
						return False
					else :
						return True
				else:
					if (msg['command'] == commands.ERR):
						print("Error : ERR msg:", msg)
						break
					else:
						print("Error : unexpected MSG:", msg)
		self.ssock.release_reader() #
		self.ssock.release_writer() #
		print("Error: can't take init_static")
		return False


	def extend_mesh_send(self,syncronus=False): # отправляет команду EXTEND_MESH c параметрами на сервер
		if not syncronus: self.syncronized=False
		return self.ssock.send_simple(commands.EXTEND_MESH)
	def extend_mesh(self): # отправляет команду EXTEND_MESH на сервер и дожидается и принимает ответ
		self.ssock.lock_writer() # блокируем отправку команд - чтобы никто не вызвал нам чего-то ещё
		self.ssock.lock_reader() # блокмруем чтение команд - чтобы никто не перехватил наши ответы сервера (асинхронные ридеры)
		self.sync() # дожидается выполнения прежних команд, при этом выкидывает ответы от них
		if self.extend_mesh_send(syncronus=True):
			while True:
				msg=self.ssock.read_msg(nolock=True) # nolock=True - мы уже в критической секции, без этого флага получим deadlock
				if Debug: print("MSG:", msg)
				if msg['command'] == commands.EXTEND_MESH:
					self.ssock.release_reader() #
					self.ssock.release_writer() #
					ecode=struct.unpack(self.ssock.mainstruct,msg['main'])[2]
					if ecode != 0 :
						print("Error on server while extend_mesh: ",  ecode)
						return False
					else :
						return True
				else:
					if (msg['command'] == commands.ERR):
						print("Error : ERR msg:", msg)
						break
					else:
						print("Error : unexpected MSG:", msg)
		self.ssock.release_reader() #
		self.ssock.release_writer() #
		print("Error: can't take extend_mesh")
		return False


	def write_static_send(self,gs1_path=None,syncronus=False): # отправляет команду WRITE_STATIC c параметрами на сервер
		if not syncronus: self.syncronized=False
		if (gs1_path is None):
			return False
		else:
			dc={'gs1_path':str(gs1_path)}
			return self.ssock.send_dict(commands.WRITE_STATIC,dc)
	def write_static(self,gs1_path=None): # отправляет команду WRITE_STATIC на сервер и дожидается и принимает ответ
		self.ssock.lock_writer() # блокируем отправку команд - чтобы никто не вызвал нам чего-то ещё
		self.ssock.lock_reader() # блокмруем чтение команд - чтобы никто не перехватил наши ответы сервера (асинхронные ридеры)
		self.sync() # дожидается выполнения прежних команд, при этом выкидывает ответы от них
		if self.write_static_send(gs1_path=gs1_path,syncronus=True):
			while True:
				msg=self.ssock.read_msg(nolock=True) # nolock=True - мы уже в критической секции, без этого флага получим deadlock
				if Debug: print("MSG:", msg)
				if msg['command'] == commands.WRITE_STATIC:
					self.ssock.release_reader() #
					self.ssock.release_writer() #
					ecode=struct.unpack(self.ssock.mainstruct,msg['main'])[2]
					if ecode != 0 :
						print("Error on server while write_static: ",  ecode)
						return False
					else :
						return True
				else:
					if (msg['command'] == commands.ERR):
						print("Error : ERR msg:", msg)
						break
					else:
						print("Error : unexpected MSG:", msg)
		self.ssock.release_reader() #
		self.ssock.release_writer() #
		print("Error: can't take write_static")
		return False


	def write_dynamic_send(self,gs1_path=None,syncronus=False): # отправляет команду WRITE_DYNAMIC c параметрами на сервер
		if not syncronus: self.syncronized=False
		if (gs1_path is None):
			return False
		else:
			dc={'gs1_path':str(gs1_path)}
			return self.ssock.send_dict(commands.WRITE_DYNAMIC,dc)
	def write_dynamic(self,gs1_path=None): # отправляет команду WRITE_DYNAMIC на сервер и дожидается и принимает ответ
		self.ssock.lock_writer() # блокируем отправку команд - чтобы никто не вызвал нам чего-то ещё
		self.ssock.lock_reader() # блокмруем чтение команд - чтобы никто не перехватил наши ответы сервера (асинхронные ридеры)
		self.sync() # дожидается выполнения прежних команд, при этом выкидывает ответы от них
		if self.write_dynamic_send(gs1_path=gs1_path,syncronus=True):
			while True:
				msg=self.ssock.read_msg(nolock=True) # nolock=True - мы уже в критической секции, без этого флага получим deadlock
				if Debug: print("MSG:", msg)
				if msg['command'] == commands.WRITE_DYNAMIC:
					self.ssock.release_reader() #
					self.ssock.release_writer() #
					ecode=struct.unpack(self.ssock.mainstruct,msg['main'])[2]
					if ecode != 0 :
						print("Error on server while write_dynamic: ",  ecode)
						return False
					else :
						return True
				else:
					if (msg['command'] == commands.ERR):
						print("Error : ERR msg:", msg)
						break
					else:
						print("Error : unexpected MSG:", msg)
		self.ssock.release_reader() #
		self.ssock.release_writer() #
		print("Error: can't take write_dynamic")
		return False


	def write_mesh_send(self,gs1_path=None,syncronus=False): # отправляет команду WRITE_MESH c параметрами на сервер
		if not syncronus: self.syncronized=False
		if (gs1_path is None):
			return False
		else:
			dc={'gs1_path':str(gs1_path)}
			return self.ssock.send_dict(commands.WRITE_MESH,dc)
	def write_mesh(self,gs1_path=None): # отправляет команду WRITE_MESH на сервер и дожидается и принимает ответ
		self.ssock.lock_writer() # блокируем отправку команд - чтобы никто не вызвал нам чего-то ещё
		self.ssock.lock_reader() # блокмруем чтение команд - чтобы никто не перехватил наши ответы сервера (асинхронные ридеры)
		self.sync() # дожидается выполнения прежних команд, при этом выкидывает ответы от них
		if self.write_mesh_send(gs1_path=gs1_path,syncronus=True):
			while True:
				msg=self.ssock.read_msg(nolock=True) # nolock=True - мы уже в критической секции, без этого флага получим deadlock
				if Debug: print("MSG:", msg)
				if msg['command'] == commands.WRITE_MESH:
					self.ssock.release_reader() #
					self.ssock.release_writer() #
					ecode=struct.unpack(self.ssock.mainstruct,msg['main'])[2]
					if ecode != 0 :
						print("Error on server while write_mesh: ",  ecode)
						return False
					else :
						return True
				else:
					if (msg['command'] == commands.ERR):
						print("Error : ERR msg:", msg)
						break
					else:
						print("Error : unexpected MSG:", msg)
		self.ssock.release_reader() #
		self.ssock.release_writer() #
		print("Error: can't take write_mesh")
		return False


	def write_send(self,gs1_path=None,syncronus=False): # отправляет команду WRITE c параметрами на сервер
		if not syncronus: self.syncronized=False
		if (gs1_path is None):
			return False
		else:
			dc={'gs1_path':str(gs1_path)}
			return self.ssock.send_dict(commands.WRITE,dc)
	def write(self,gs1_path=None): # отправляет команду WRITE на сервер и дожидается и принимает ответ
		self.ssock.lock_writer() # блокируем отправку команд - чтобы никто не вызвал нам чего-то ещё
		self.ssock.lock_reader() # блокмруем чтение команд - чтобы никто не перехватил наши ответы сервера (асинхронные ридеры)
		self.sync() # дожидается выполнения прежних команд, при этом выкидывает ответы от них
		if self.write_send(gs1_path=gs1_path,syncronus=True):
			while True:
				msg=self.ssock.read_msg(nolock=True) # nolock=True - мы уже в критической секции, без этого флага получим deadlock
				if Debug: print("MSG:", msg)
				if msg['command'] == commands.WRITE:
					self.ssock.release_reader() #
					self.ssock.release_writer() #
					ecode=struct.unpack(self.ssock.mainstruct,msg['main'])[2]
					if ecode != 0 :
						print("Error on server while write: ",  ecode)
						return False
					else :
						return True
				else:
					if (msg['command'] == commands.ERR):
						print("Error : ERR msg:", msg)
						break
					else:
						print("Error : unexpected MSG:", msg)
		self.ssock.release_reader() #
		self.ssock.release_writer() #
		print("Error: can't take write")
		return False


	def read_send(self,gs1_path=None,syncronus=False): # отправляет команду READ c параметрами на сервер
		if not syncronus: self.syncronized=False
		if (gs1_path is None):
			return False
		else:
			dc={'gs1_path':str(gs1_path)}
			return self.ssock.send_dict(commands.READ,dc)
	def read(self,gs1_path=None): # отправляет команду READ на сервер и дожидается и принимает ответ
		self.ssock.lock_writer() # блокируем отправку команд - чтобы никто не вызвал нам чего-то ещё
		self.ssock.lock_reader() # блокмруем чтение команд - чтобы никто не перехватил наши ответы сервера (асинхронные ридеры)
		self.sync() # дожидается выполнения прежних команд, при этом выкидывает ответы от них
		if self.read_send(gs1_path=gs1_path,syncronus=True):
			while True:
				msg=self.ssock.read_msg(nolock=True) # nolock=True - мы уже в критической секции, без этого флага получим deadlock
				if Debug: print("MSG:", msg)
				if msg['command'] == commands.READ:
					self.ssock.release_reader() #
					self.ssock.release_writer() #
					ecode=struct.unpack(self.ssock.mainstruct,msg['main'])[2]
					if ecode != 0 :
						print("Error on server while read: ",  ecode)
						return False
					else :
						return True
				else:
					if (msg['command'] == commands.ERR):
						print("Error : ERR msg:", msg)
						break
					else:
						print("Error : unexpected MSG:", msg)
		self.ssock.release_reader() #
		self.ssock.release_writer() #
		print("Error: can't take read")
		return False


	def set_solver_send(self,solver=None,syncronus=False): # отправляет команду SET_SOLVER c параметрами на сервер
		if not syncronus: self.syncronized=False
		if (solver is None):
			return False
		else:
			dc={'solver':str(solver)}
			return self.ssock.send_dict(commands.SET_SOLVER,dc)
	def set_solver(self,solver=None): # отправляет команду SET_SOLVER на сервер и дожидается и принимает ответ
		self.ssock.lock_writer() # блокируем отправку команд - чтобы никто не вызвал нам чего-то ещё
		self.ssock.lock_reader() # блокмруем чтение команд - чтобы никто не перехватил наши ответы сервера (асинхронные ридеры)
		self.sync() # дожидается выполнения прежних команд, при этом выкидывает ответы от них
		if self.set_solver_send(solver=solver,syncronus=True):
			while True:
				msg=self.ssock.read_msg(nolock=True) # nolock=True - мы уже в критической секции, без этого флага получим deadlock
				if Debug: print("MSG:", msg)
				if msg['command'] == commands.SET_SOLVER:
					self.ssock.release_reader() #
					self.ssock.release_writer() #
					ecode=struct.unpack(self.ssock.mainstruct,msg['main'])[2]
					if ecode != 0 :
						print("Error on server while set_solver: ",  ecode)
						return False
					else :
						return True
				else:
					if (msg['command'] == commands.ERR):
						print("Error : ERR msg:", msg)
						break
					else:
						print("Error : unexpected MSG:", msg)
		self.ssock.release_reader() #
		self.ssock.release_writer() #
		print("Error: can't take set_solver")
		return False


	def read_info_send(self,gs1_path=None,syncronus=False): # отправляет команду READ_INFO c параметрами на сервер
		if not syncronus: self.syncronized=False
		if (gs1_path is None):
			return False
		else:
			dc={'gs1_path':str(gs1_path)}
			return self.ssock.send_dict(commands.READ_INFO,dc)
	def read_info(self,gs1_path=None): # отправляет команду READ_INFO на сервер и дожидается и принимает ответ
		self.ssock.lock_writer() # блокируем отправку команд - чтобы никто не вызвал нам чего-то ещё
		self.ssock.lock_reader() # блокмруем чтение команд - чтобы никто не перехватил наши ответы сервера (асинхронные ридеры)
		self.sync() # дожидается выполнения прежних команд, при этом выкидывает ответы от них
		if self.read_info_send(gs1_path=gs1_path,syncronus=True):
			while True:
				msg=self.ssock.read_msg(nolock=True) # nolock=True - мы уже в критической секции, без этого флага получим deadlock
				if Debug: print("MSG:", msg)
				if msg['command'] == commands.READ_INFO:
					self.ssock.release_reader() #
					self.ssock.release_writer() #
					ecode=struct.unpack(self.ssock.mainstruct,msg['main'])[2]
					if ecode != 0 :
						print("Error on server while read_info: ",  ecode)
						return False
					else :
						return True
				else:
					if (msg['command'] == commands.ERR):
						print("Error : ERR msg:", msg)
						break
					else:
						print("Error : unexpected MSG:", msg)
		self.ssock.release_reader() #
		self.ssock.release_writer() #
		print("Error: can't take read_info")
		return False

	def read_mesh_send(self,gs1_path=None,syncronus=False): # отправляет команду READ_MESH c параметрами на сервер
		if not syncronus: self.syncronized=False
		if (gs1_path is None):
			return False
		else:
			dc={'gs1_path':str(gs1_path)}
			return self.ssock.send_dict(commands.READ_MESH,dc)
	def read_mesh(self,gs1_path=None): # отправляет команду READ_MESH на сервер и дожидается и принимает ответ
		self.ssock.lock_writer() # блокируем отправку команд - чтобы никто не вызвал нам чего-то ещё
		self.ssock.lock_reader() # блокмруем чтение команд - чтобы никто не перехватил наши ответы сервера (асинхронные ридеры)
		self.sync() # дожидается выполнения прежних команд, при этом выкидывает ответы от них
		if self.read_mesh_send(gs1_path=gs1_path,syncronus=True):
			while True:
				msg=self.ssock.read_msg(nolock=True) # nolock=True - мы уже в критической секции, без этого флага получим deadlock
				if Debug: print("MSG:", msg)
				if msg['command'] == commands.READ_MESH:
					self.ssock.release_reader() #
					self.ssock.release_writer() #
					ecode=struct.unpack(self.ssock.mainstruct,msg['main'])[2]
					if ecode != 0 :
						print("Error on server while read_mesh: ",  ecode)
						return False
					else :
						return True
				else:
					if (msg['command'] == commands.ERR):
						print("Error : ERR msg:", msg)
						break
					else:
						print("Error : unexpected MSG:", msg)
		self.ssock.release_reader() #
		self.ssock.release_writer() #
		print("Error: can't take read_mesh")
		return False

#GET_PROBE_FIELDS {'zone_number':0,'probe_name':'dot1','binary':false}
	def get_probe_fields_send(self,zone_number=None,probe_name=None,binary=False,syncronus=False): # отправляет команду GET_PROBE_FIELDS c параметрами на сервер
		if not syncronus: self.syncronized=False
		if (zone_number is None)or(probe_name is None):
			return False
		else:
			dc={"zone_number":zone_number,"probe_name":probe_name,"binary":binary}
			return self.ssock.send_dict(commands.GET_PROBE_FIELDS,dc)
	def get_probe_fields(self,zone_number=None,probe_name=None,binary=False): # отправляет команду GET_PROBE_FIELDS на сервер и дожидается и принимает ответ
		self.ssock.lock_writer() # блокируем отправку команд - чтобы никто не вызвал нам чего-то ещё
		self.ssock.lock_reader() # блокмруем чтение команд - чтобы никто не перехватил наши ответы сервера (асинхронные ридеры)
		self.sync() # дожидается выполнения прежних команд, при этом выкидывает ответы от них
		if self.get_probe_fields_send(zone_number=zone_number,probe_name=probe_name,binary=binary,syncronus=True):
			ret = {}
			while True:
				msg = self.ssock.read_msg(
					nolock=True)  # nolock=True - мы уже в критической секции, без этого флага получим deadlock
				if Debug: print("MSG:", msg)
				if msg['command'] == commands.PROBE_FIELD:
					try:
						ret = eval(msg['param'].decode("utf-8")[0:-1])
					except :
						print("Error : param not decoded:", msg['param'])
						break
				else:
					if msg['command'] == commands.GET_PROBE_FIELDS:
						self.ssock.release_reader()  #
						self.ssock.release_writer()  #
						ecode = struct.unpack(self.ssock.mainstruct, msg['main'])[2]
						if ecode != 0:
							print("Error on server while take get_probe_fields: ", ecode)
							return {'err': "Error on server while take get_probe_fields", 'errcode': ecode}
						else:
							return ret
					else:
						if (msg['command'] == commands.ERR):
							print("Error : ERR msg:", msg)
							break
						else:
							print("Error : unexpected MSG:", msg)
		self.ssock.release_reader()  #
		self.ssock.release_writer()  #
		return {'err': "Error can't take get_probe_fields", 'errcode': -9999}
	


	def set_probe_send(self,zone_number=None,probe_name=None,position_begin=None,position_end=None,fields_type=None,fields=None,integrals=[],syncronus=False): # отправляет команду SET_PROBE c параметрами на сервер
		if not syncronus: self.syncronized=False
		if (zone_number is None)or(probe_name is None)or(position_begin is None)or(position_end is None)or(fields_type is None):
			return False
		if (not isinstance(position_begin, list)) or (not isinstance(position_end, list)):
			return False
		if (not (len(position_begin)==3)) or (not (len(position_end)==3)):
			return False
		else:
			dc={"zone_number":zone_number,"probe_name":probe_name,"position_begin":position_begin,"position_end":position_end,"fields_type":fields_type.value}
			if not (fields is None):
				dc['fields']=fields
			if not (integrals is None):
				dc['integrals']=integrals
			return self.ssock.send_dict(commands.SET_PROBE,dc)
	def set_probe(self,zone_number=None,probe_name=None,position_begin=None,position_end=None,fields_type=None,fields=None,integrals=[]): # отправляет команду SET_PROBE на сервер и дожидается и принимает ответ
		self.ssock.lock_writer() # блокируем отправку команд - чтобы никто не вызвал нам чего-то ещё
		self.ssock.lock_reader() # блокмруем чтение команд - чтобы никто не перехватил наши ответы сервера (асинхронные ридеры)
		self.sync() # дожидается выполнения прежних команд, при этом выкидывает ответы от них
		if self.set_probe_send(zone_number=zone_number,probe_name=probe_name,position_begin=position_begin,position_end=position_end,fields_type=fields_type,fields=fields,integrals=integrals,syncronus=True):
			while True:
				msg=self.ssock.read_msg(nolock=True) # nolock=True - мы уже в критической секции, без этого флага получим deadlock
				if Debug: print("MSG:", msg)
				if msg['command'] == commands.SET_PROBE:
					self.ssock.release_reader() #
					self.ssock.release_writer() #
					ecode=struct.unpack(self.ssock.mainstruct,msg['main'])[2]
					if ecode != 0 :
						return {'err': "Error on server while set_probe", 'errcode': -9998}
					else :
						return eval(msg['param'].decode("utf-8")[0:-1])
				else:
					if (msg['command'] == commands.ERR):
						print("Error : ERR msg:", msg)
						break
					else:
						print("Error : unexpected MSG:", msg)
		self.ssock.release_reader() #
		self.ssock.release_writer() #
		return {'err':"Error can't take set_probe",'errcode':-9999}


	def set_data_param_send(self,parametr_name=None,parametr_value=None,syncronus=False): # отправляет команду SET_DATA_PARAM c параметрами на сервер
		if not syncronus: self.syncronized=False
		if (parametr_name is None)or(parametr_value is None):
			print("Error on server while take set_data_param: ", 9996)
			return False
		else:
			dc={"parametr_name":parametr_name,"parametr_value":parametr_value}
			if Debug: print("SEND:", dc)
			return self.ssock.send_dict(commands.SET_DATA_PARAM,dc)
	def set_data_param(self,parametr_name=None,parametr_value=None): # отправляет команду SET_DATA_PARAM на сервер и дожидается и принимает ответ
		self.ssock.lock_writer() # блокируем отправку команд - чтобы никто не вызвал нам чего-то ещё
		self.ssock.lock_reader() # блокмруем чтение команд - чтобы никто не перехватил наши ответы сервера (асинхронные ридеры)
		self.sync() # дожидается выполнения прежних команд, при этом выкидывает ответы от них
		if self.set_data_param_send(parametr_name=parametr_name,parametr_value=parametr_value,syncronus=True):
			ret = {}
			while True:
				msg = self.ssock.read_msg(nolock=True)  # nolock=True - мы уже в критической секции, без этого флага получим deadlock
				if Debug: print("MSG:", msg)
				if msg['command'] == commands.UPDATE_DATA_INFORMATION:
					ret = eval(msg['param'].decode("utf-8")[0:-1])
				else:
					if msg['command'] == commands.SET_DATA_PARAM:
						self.ssock.release_reader()  #
						self.ssock.release_writer()  #
						ecode = struct.unpack(self.ssock.mainstruct, msg['main'])[2]
						if ecode != 0:
							print("Error on server while take set_data_param: ", ecode)
							return {'err': "Error on server while take set_data_param", 'errcode': ecode}
						else:
							return ret
					else:
						if (msg['command'] == commands.ERR):
							print("Error : ERR msg:", msg)
							break
						else:
							print("Error : unexpected MSG:", msg)
		self.ssock.release_reader() #
		self.ssock.release_writer() #
		return {'err':"Error can't take set_data_param",'errcode':-9999}

	def set_zone_param_send(self,parametr_name=None,parametr_value=None,zone_name=None,zone_index=None,syncronus=False): # отправляет команду SET_ZONE_PARAM c параметрами на сервер
		if not syncronus: self.syncronized=False
		if (parametr_name is None)or(parametr_value is None):
			print("Error on server while take set_zone_param: ", 9997)
			return False
		if (not (zone_name is None))and(not (zone_index is None)):
			print("Error on server while take set_zone_param: ", 9996)
			return False
		dc={"parametr_name":parametr_name,"parametr_value":parametr_value}
		if not (zone_name is None):
			dc["zone_name"]=zone_name
		if not (zone_index is None):
			dc["zone_index"]=zone_index
		if Debug: print("SEND:", dc)
		return self.ssock.send_dict(commands.SET_ZONE_PARAM,dc)
	
	def set_zone_param(self,parametr_name=None,parametr_value=None,zone_name=None,zone_index=None): # отправляет команду SET_ZONE_PARAM на сервер и дожидается и принимает ответ
		self.ssock.lock_writer() # блокируем отправку команд - чтобы никто не вызвал нам чего-то ещё
		self.ssock.lock_reader() # блокмруем чтение команд - чтобы никто не перехватил наши ответы сервера (асинхронные ридеры)
		self.sync() # дожидается выполнения прежних команд, при этом выкидывает ответы от них
		if self.set_zone_param_send(parametr_name=parametr_name,parametr_value=parametr_value,zone_name=zone_name,zone_index=zone_index,syncronus=True):
			ret = {}
			while True:
				msg = self.ssock.read_msg(nolock=True)  # nolock=True - мы уже в критической секции, без этого флага получим deadlock
				if Debug: print("MSG:", msg)
				if msg['command'] == commands.UPDATE_ZONE_INFORMATION:
					ret = eval(msg['param'].decode("utf-8")[0:-1])
				else:
					if msg['command'] == commands.SET_ZONE_PARAM:
						self.ssock.release_reader()  #
						self.ssock.release_writer()  #
						ecode = struct.unpack(self.ssock.mainstruct, msg['main'])[2]
						if ecode != 0:
							print("Error on server while take set_zone_param: ", ecode)
							print ({"parametr_name":parametr_name,"parametr_value":parametr_value,"zone_name":zone_name,"zone_index":zone_index})
							return {'err': "Error on server while take set_zone_param", 'errcode': ecode}
						else:
							return ret
					else:
						if (msg['command'] == commands.ERR):
							print("Error : ERR msg:", msg)
							break
						else:
							print("Error : unexpected MSG:", msg)
		self.ssock.release_reader() #
		self.ssock.release_writer() #
		return {'err':"Error can't take set_zone_param",'errcode':-9999}


	def set_boundary_param_send(self,parametr_name=None,parametr_value=None,zone_name=None,zone_index=None,boundary_name=None,boundary_index=None,syncronus=False): # отправляет команду SET_BOUNDARY_PARAM c параметрами на сервер
		if not syncronus: self.syncronized=False
		if (parametr_name is None)or(parametr_value is None):
			print("Error on server while take set_boundary_param: ", 9997)
			return False
		if (not (zone_name is None))and(not (zone_index is None)):
			print("Error on server while take set_boundary_param: ", 9996)
			return False
		if (not (boundary_name is None))and(not (boundary_index is None)):
			print("Error on server while take set_boundary_param: ", 9995)
			return False
		dc={"parametr_name":parametr_name,"parametr_value":parametr_value}
		if not (zone_name is None):
			dc["zone_name"]=zone_name
		if not (zone_index is None):
			dc["zone_index"]=zone_index
		if not (boundary_name is None):
			dc["boundary_name"]=boundary_name
		if not (boundary_index is None):
			dc["boundary_index"]=boundary_index
		if Debug: print("SEND:", dc)
		return self.ssock.send_dict(commands.SET_BOUNDARY_PARAM,dc)
	def set_boundary_param(self,parametr_name=None,parametr_value=None,zone_name=None,zone_index=None,boundary_name=None,boundary_index=None): # отправляет команду SET_BOUNDARY_PARAM на сервер и дожидается и принимает ответ
		self.ssock.lock_writer() # блокируем отправку команд - чтобы никто не вызвал нам чего-то ещё
		self.ssock.lock_reader() # блокмруем чтение команд - чтобы никто не перехватил наши ответы сервера (асинхронные ридеры)
		self.sync() # дожидается выполнения прежних команд, при этом выкидывает ответы от них
		if self.set_boundary_param_send(parametr_name=parametr_name,parametr_value=parametr_value,zone_name=zone_name,zone_index=zone_index,boundary_name=boundary_name,boundary_index=boundary_index,syncronus=True):
			ret = {}
			while True:
				msg = self.ssock.read_msg(nolock=True)  # nolock=True - мы уже в критической секции, без этого флага получим deadlock
				if Debug: print("MSG:", msg)
				if msg['command'] == commands.UPDATE_BOUNDARY_INFORMATION:
					ret = eval(msg['param'].decode("utf-8")[0:-1])
				else:
					if msg['command'] == commands.SET_BOUNDARY_PARAM:
						self.ssock.release_reader()  #
						self.ssock.release_writer()  #
						ecode = struct.unpack(self.ssock.mainstruct, msg['main'])[2]
						if ecode != 0:
							print("Error on server while take set_boundary_param: ", ecode)
							return {'err': "Error on server while take set_boundary_param", 'errcode': ecode}
						else:
							return ret
					else:
						if (msg['command'] == commands.ERR):
							print("Error : ERR msg:", msg)
							break
						else:
							print("Error : unexpected MSG:", msg)
		self.ssock.release_reader() #
		self.ssock.release_writer() #
		return {'err':"Error can't take set_boundary_param",'errcode':-9999}

	def get_controls_send(self,syncronus=False): # отправляет команду GET_CONTROLS c параметрами на сервер
		if not syncronus: self.syncronized=False
		return self.ssock.send_simple(commands.GET_CONTROLS)
	def get_controls(self): # отправляет команду GET_CONTROLS на сервер и дожидается и принимает ответ
		self.ssock.lock_writer() # блокируем отправку команд - чтобы никто не вызвал нам чего-то ещё
		self.ssock.lock_reader() # блокмруем чтение команд - чтобы никто не перехватил наши ответы сервера (асинхронные ридеры)
		self.sync() # дожидается выполнения прежних команд, при этом выкидывает ответы от них
		if self.get_controls_send(syncronus=True):
			while True:
				msg=self.ssock.read_msg(nolock=True) # nolock=True - мы уже в критической секции, без этого флага получим deadlock
				if Debug: print("MSG:", msg)
				if msg['command'] == commands.GET_CONTROLS:
					self.ssock.release_reader() #
					self.ssock.release_writer() #
					ret = eval(msg['param'].decode("utf-8")[0:-1])
					return ret
				else:
					if (msg['command'] == commands.ERR):
						print("Error : ERR msg:", msg)
						break
					else:
						print("Error : unexpected MSG:", msg)
		self.ssock.release_reader() #
		self.ssock.release_writer() #
		return {'err':"Error can't take calc_start_step",'errcode':-9999}



	def set_wd_send(self,wd_path=None,syncronus=False): # отправляет команду SET_WD c параметрами на сервер
		if not syncronus: self.syncronized=False
		if (wd_path is None):
			return False
		else:
			dc={'wd_path':str(wd_path)}
			return self.ssock.send_dict(commands.SET_WD,dc)
	def set_wd(self,wd_path=None): # отправляет команду SET_WD на сервер и дожидается и принимает ответ
		self.ssock.lock_writer() # блокируем отправку команд - чтобы никто не вызвал нам чего-то ещё
		self.ssock.lock_reader() # блокмруем чтение команд - чтобы никто не перехватил наши ответы сервера (асинхронные ридеры)
		self.sync() # дожидается выполнения прежних команд, при этом выкидывает ответы от них
		if self.set_wd_send(wd_path=wd_path,syncronus=True):
			while True:
				msg=self.ssock.read_msg(nolock=True) # nolock=True - мы уже в критической секции, без этого флага получим deadlock
				if Debug: print("MSG:", msg)
				if msg['command'] == commands.SET_WD:
					self.ssock.release_reader() #
					self.ssock.release_writer() #
					ecode=struct.unpack(self.ssock.mainstruct,msg['main'])[2]
					if ecode != 0 :
						print("Error on server while chdir: ",  ecode)
						return False
					else :
						return True
				else:
					if (msg['command'] == commands.ERR):
						print("Error : ERR msg:", msg)
						break
					else:
						print("Error : unexpected MSG:", msg)
		self.ssock.release_reader() #
		self.ssock.release_writer() #
		print("Error: can't make chdir")
		return False


	def terminate(self):
		print ("terminate")
		return self.ssock.terminate()



	def connect_to_socket(self,host,port):
		if Debug: print ("connect_to_socket",host,port)
		return self.ssock.connect_to_socket(host,port)

	def run_local(self,port):
		print ("run_local")
		print ("Error")
	def run_local_mpi(self,host,port):
		print ("run_local_mpi")
		print ("Error")

	def get_exec_info(self):
		print ("Error")


	def __init__(self):
		if Debug: print ("program constructor")
		self.ssock = gs1_supersock()

	def __del__(self):
		if Debug: print ("program destructor")



#print (repr(commands.HELP))
#print ((commands.HELP.name))
#print ((commands(1).name))
#print ((commands.HELP.value))

import json

class config_processor:
	def __init__(self,config_file):
		self.solver = gs1()
		self.config_file=config_file
		self.config=None
		try:
			with open(config_file) as f:
				data = json.load(f)
				self.config=data
		except Exception as e:
			print("Ошибка инициализации скрипта управления сеткопостроителем")
			traceback.print_exc(file=sys.stdout)
	def write_config (self, path = None):
		if (path is None): path=self.config_file

		try:
			with open(path) as f:
				json.dump(self.config, f)
		except Exception as e:
			print("Ошибка записи конфига")
			traceback.print_exc(file=sys.stdout)
	def do_tasks(self):
		for task in self.config["tasks"]["Task List"]:
			print (task["Type"]+ " " + task["Command"])
			if (task["Type"] == "gs1_command" ):
				getattr(self.solver, task["Command"])(**(task["Arguments"]))
			elif (task["Type"] == "action" ):
				getattr(self, task["Command"])(**(task["Arguments"]))
				#self.do_action(task["Command"], task["Arguments"])
			else:
				print ("Неизвестный тип команды" + task["Type"])
				raise NameError("Неизвестный тип команды")
	def distribute_parameters(self):
		for data_prm, data_val in self.config["Solution Conditions"].items():
			data_vals = data_val
			if not (isinstance(data_val, str) or isinstance(data_val, int) or isinstance(data_val, float)):
				data_vals = json.dumps(data_val)
			self.solver.set_data_param(parametr_name=data_prm, parametr_value=data_vals)
		for zone_name, zone_config in self.config["Zone Conditions"].items():
			for data_prm, data_val in zone_config.items():
				data_vals = data_val
				if not (isinstance(data_val, str) or isinstance(data_val, int) or isinstance(data_val, float)):
					data_vals = json.dumps(data_val)
				if isinstance(zone_name,str):
					self.solver.set_zone_param(zone_name=zone_name, parametr_name = data_prm, parametr_value = data_vals)
				elif isinstance(zone_name,int):
					self.solver.set_zone_param(zone_index=zone_name, parametr_name = data_prm, parametr_value = data_vals)
				else:
					print ("Неизвестный идентификатор зоны" + str(zone_name))
					raise NameError("Неизвестный идентификатор зоны")
		for boundary_id, boundary_config in self.config["Boundary Conditions"].items():
			for data_prm, data_val in boundary_config.items():
				data_vals = data_val
				if not (isinstance(data_val, str) or isinstance(data_val, int) or isinstance(data_val, float)):
					data_vals = json.dumps(data_val)
				if isinstance(boundary_id,str):
					self.solver.set_boundary_param(boundary_name=boundary_id, parametr_name = data_prm, parametr_value = data_vals)
				elif isinstance(boundary_id,list):
					if len(boundary_id) == 2:
						[zone_name,boundary_name] = boundary_id
						if isinstance(zone_name, str) and isinstance(boundary_name, str):
							self.solver.set_boundary_param(zone_name=zone_name, boundary_name=boundary_name, parametr_name = data_prm, parametr_value = data_vals)
						elif isinstance(zone_name, int) and isinstance(boundary_name, int):
							self.solver.set_boundary_param(zone_index=zone_name, boundary_index=boundary_name, parametr_name = data_prm, parametr_value = data_vals)
						else:
							print ("Неверный идентификатор границы" + str(boundary_id))
							raise NameError("Неверный идентификатор границы")
					else:
						print ("Неверный идентификатор границы" + str(boundary_id))
						raise NameError("Неверный идентификатор границы")
				else:
						print ("Неверный идентификатор границы" + str(boundary_id))
						raise NameError("Неверный идентификатор границы")
	def set_config_data_conditions(self,parametr_name,parametr_value):
		self.config["Solution Conditions"][parametr_name]=parametr_value
	def set_config_zone_conditions(self,parametr_name,parametr_value,zone_name=None):
		for cur_zone_name, cur_zone_config in self.config["Zone Conditions"].items():
			if (zone_name is None) or (zone_name == cur_zone_name):
				cur_zone_config[parametr_name]=parametr_value
	def set_config_boundary_conditions(self,parametr_name,parametr_value,boundary_name=None):
		for cur_boundary_name, cur_boundary_config in self.config["Boundary Conditions"].items():
			if (boundary_name is None) or (boundary_name == cur_boundary_name):
				cur_boundary_config[parametr_name]=parametr_value
	def dump_config(self,new_file=None):
		if not (new_file is None):
			self.config_file=new_file
		try:
			with open(self.config_file,"w") as f:
				json.dump(self.config, f, ensure_ascii=False, sort_keys=True, indent=4, separators=(',', ': '))
		except Exception as e:
			print("Ошибка записи конфигурационного файла:",self.config_file)
			traceback.print_exc(file=sys.stdout)

