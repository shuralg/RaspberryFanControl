#!/usr/bin/env python

import sys
from daemon3x import daemon
import RPi.GPIO as GPIO                     # Импортируем библиотеку по работе с GPIO
import traceback                       # Импортируем библиотеки для обработки исключений

from time import sleep                      # Импортируем библиотеку для работы со временем
from re import findall                      # Импортируем библиотеку по работе с регулярными выражениями
from subprocess import check_output         # Импортируем библиотеку по работе с внешними процессами

import config 


def get_temp():
    temp = check_output(["/opt/vc/bin/vcgencmd","measure_temp"]).decode()    # Выполняем запрос температуры
    temp = float(findall('\d+\.\d+', temp)[0])                   # Извлекаем при помощи регулярного выражения значение температуры из строки "temp=47.8'C"
    return temp                            # Возвращаем результат
    

class CoolerControlDaemon(daemon):
	
	# def stop(self):
		# if self._GPIO is not None:
			# self._GPIO.cleanup()                          # Возвращаем пины в исходное состояние
		# else:
			# print("self._GPIO is not None")
		# super().stop()
		
	# def get_state(self):
		# print("Temperature = {}, Fan is work? {}".format(self._temper, self._state_fan))
		# #print (get_temp())
	
	def run(self):
		flag = True
		try:
			tempOn = config.tempOn                  # Температура включения кулера
			tempDelta = config.tempDelta			# Разница температур включения и выключения кулера
			controlPin = config.controlPin          # Пин отвечающий за управление
			pinState = config.pinState              # Актуальное состояние кулера
			time_to_sleep = config.time_to_sleep	# Пауза
		except:
			flag = False
			self.stop()
			
		try:
			# === Инициализация пинов ===
			GPIO.setmode(GPIO.BCM)                  # Режим нумерации в BCM
			GPIO.setup(controlPin, GPIO.OUT, initial=0) # Управляющий пин в режим OUTPUT
			self._GPIO = GPIO
		except:
			flag = False
			self.stop()
		
		self._temper = get_temp()
			
		if flag:
			try:
				while True:                             # Бесконечный цикл запроса температуры
					temp = get_temp()                   # Получаем значение температуры

					if temp > tempOn and not pinState or temp < tempOn - tempDelta and pinState:
						pinState = not pinState         # Меняем статус состояния
						GPIO.output(controlPin, pinState) # Задаем новый статус пину управления

					sleep(time_to_sleep)                            # Пауза

			finally:
				GPIO.cleanup()

if __name__ == "__main__":
	daemon = CoolerControlDaemon('/tmp/cooler_control_daemon.pid')
	if len(sys.argv) == 2:
		if 'start' == sys.argv[1]:
			daemon.start()
		elif 'stop' == sys.argv[1]:
			daemon.stop()
		elif 'restart' == sys.argv[1]:
			daemon.restart()
		# elif 'state' == sys.argv[1]:
			# daemon.get_state()
		else:
			print("Unknown command")
			sys.exit(2)
		sys.exit(0)
	else:
		print("usage: %s start|stop|restart" % sys.argv[0])
		sys.exit(2)
