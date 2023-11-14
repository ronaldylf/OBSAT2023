from machine import (
    Pin,
    ADC,
    SoftI2C,
    SoftSPI,
    PWM,
    reset
)
from imu import MPU6050
from time import sleep
from bmp280 import *
import network
import os
from sdcard import SDCard
import aht
from myENS160 import myENS160

class CubeSat:
    def __init__(self):
        self.battery_level = 0
        self.i2c = SoftI2C(scl=Pin(22), sda=Pin(21))
        self.spi = SoftSPI(-1,
              miso=Pin(19),
              mosi=Pin(23),
              sck=Pin(18)
        )
        self.cs = Pin(5, Pin.OUT)
        self.buzzer_gpio = 32
        self.battery_gpio = 35
    
    def reset(self):
        reset()
    
    def wifi_connect(self, ssid="", password=""):
        sta_if = network.WLAN(network.STA_IF)
        if not sta_if.isconnected():
            print(f"trying to connect in '{ssid}'")
            sta_if.active(True)
            sta_if.connect(ssid, password)
            while not sta_if.isconnected():
                pass
        print(f"connection OK with '{ssid}'")
    
    def mount_sd(self):
        self.sd = SDCard(self.spi, self.cs)
        os.mount(self.sd, '/sd')
    
    def clear_sd(self): # limpar arquivos do cartão micro SD
        for file in os.listdir('/sd'):
            if '.' in file: os.remove(f'/sd/{file}')

    def read_file(self, file_name): # lê o conteúdo de algum arquivo de texto
        with open(file_name, 'r+') as file: return file.read()

    def init_buzzer(self, freq=2000, duty=512): # inicia buzzer
        self.beeper = PWM(Pin(self.buzzer_gpio, Pin.OUT), freq=freq, duty=duty)

    def deinit_buzzer(self): # interrompe buzzer
        self.beeper.deinit()

    def beep(self, on_time=0.1, freq=4000, duty=512): # soltar bipes como indicação
        self.init_buzzer(freq, duty)
        sleep(on_time)
        self.deinit_buzzer()
    
    def get_battery_level(self): # nível da bateria em porcentagem (%)
        pot = ADC(Pin(self.battery_gpio, mode=Pin.IN))
        pot.atten(ADC.ATTN_11DB)
        self.battery_level = round((pot.read()/4095)*1.09*100, 2)
        return self.battery_level
    
    def gyroscope(self): # leitura do giroscópio
        try:
            self.mpu = MPU6050(self.i2c)
            return [
                round(self.mpu.gyro.x, 2),
                round(self.mpu.gyro.y, 2),
                round(self.mpu.gyro.z, 2)
            ]

        except Exception as e:
            print(e)
            return [-1, -1, -1]

    def acceleration(self): # leitura do acelerômetro
        try:
            self.mpu = MPU6050(self.i2c)
            return [
                round(self.mpu.accel.x, 2),
                round(self.mpu.accel.y, 2),
                round(self.mpu.accel.z, 2)
            ]
        except Exception as e:
            print(e)
            return [-1, -1, -1]

    def get_angle(self): # pegar ângulo do satélite
        import math
        self.angle = math.asin(self.acceleration()[1]/9.8)
        return self.angle
    
    def temperature(self, sensor=0): # temperatura em graus celsius
        '''
        sensor=0: lida pelo sensor mpu6050
        sensor=1: lida pelo sensor bmp280
        sensor=2: lida pelo sensor aht21
        '''
        try:
            self.temperature_ = None
            if (sensor==0):
                self.bmp = BMP280(self.i2c)
                self.bmp.use_case(BMP280_CASE_INDOOR)
                self.temperature_ = self.bmp.temperature
            elif (sensor==1):
                self.mpu = MPU6050(self.i2c)
                self.temperature_ = self.mpu.temperature
            else:
                self.aht_sensor = aht.AHT2x(self.i2c, crc=True)
                self.temperature_ = self.aht_sensor.temperature
            return round(self.temperature_, 2)
        except Exception as e:
            print(e)
            return -1
        
    def pressure(self): # pressão em pascal
        try:
            self.bmp = BMP280(self.i2c)
            self.bmp.use_case(BMP280_CASE_INDOOR)
            return self.bmp.pressure
        except Exception as e:
            print(e)
            return -1
    
    def humidity(self): # umidade em porcentagem (%)
        try:
            self.aht_sensor = aht.AHT2x(self.i2c, crc=True)
            return round(self.aht_sensor.humidity, 2)
        except Exception as e:
            print(e)
            return -1
        
    def get_air_quality(self): # leitura dos dados de qualidade do ar
        self.ens = myENS160(self.i2c)
        return {
            'TVOC': self.ens.getTVOC(),
            'AQI': self.ens.getAQI(),
            'ECO2': self.ens.getECO2()
        }

