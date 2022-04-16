import time
import json
import RPi.GPIO as IO

from paho.mqtt import client as mqtt_client

import Adafruit_DHT
sensor_name = Adafruit_DHT.DHT11
sensor_pin = 17

IO.cleanup()

motor_pin = 19

broker = 'broker.hivemq.com'
port = 1883
topic = "team3/sensors_data/primary"
topic_command = "team3/command/primary"
client_id = 'python-mqtt-poezd-pub-pi'

red_value = 0
blue_value = 0
green_value = 0

red_pin = 5
blue_pin = 13
green_pin = 6

motor_angle = 0

IO.setwarnings(False)
IO.setmode (IO.BCM)
IO.setup(motor_pin,IO.OUT)
motot_pwm = IO.PWM(motor_pin,50)
motot_pwm.start(2.5)

IO.setup(red_pin,IO.OUT)
IO.setup(blue_pin,IO.OUT)
IO.setup(green_pin,IO.OUT)
red_pwm = IO.PWM(red_pin,100)
blue_pwm = IO.PWM(blue_pin,100)
green_pwm = IO.PWM(green_pin,100)
red_pwm.start(red_value)
blue_pwm.start(blue_value)
green_pwm.start(green_value)

def prepare_angle(angle):
	if angle > 180 or angle < 0:
		return 2.5
	return 10.0/180 * angle + 2.5

def connect_mqtt():
	def on_connect(client, userdata, flags, rc):
		if rc == 0:
			print("Connected")
		else:
			print("Fail")
	client = mqtt_client.Client(client_id)
	client.on_connect = on_connect
	client.connect(broker, port)
	return client

def subscribe(client: mqtt_client):
	def on_message(client, userdata, msg):
		global motor_angle, red_value, green_value, blue_value
		request_data = json.loads(msg.payload.decode())
		if request_data["name"] == "MOTION":
			motor_angle = int(request_data["value"])
			motot_pwm.ChangeDutyCycle(prepare_angle(motor_angle))
		elif request_data["name"] == "LED":
			rgb_value = request_data["value"].split("-")
			if len(rgb_value) < 3:
				return
			red_value = int(rgb_value[0])
			green_value = int(rgb_value[1])
			blue_value = int(rgb_value[2])
			red_pwm.start(int(red_value/255.0*100))
			blue_pwm.start(int(blue_value/255.0*100))
			green_pwm.start(int(green_value/255.0*100))


	client.subscribe(topic_command)
	client.on_message = on_message


client = connect_mqtt()
subscribe(client)
client.loop_start()

while True:
	humidity, temperature = Adafruit_DHT.read_retry(sensor_name, sensor_pin)
	temp = '%.1f' % temperature
	hum = '%.1f' % humidity
	led = "%i-%i-%i" % (red_value, green_value, blue_value)
	mot = "%i" % motor_angle
	data = json.dumps(
		[
			{
				"name": "TEMPERATURE",
				"value": temp
			},
			{
				"name": "HUMIDITY",
				"value": hum
			},
            {
				"name": "LED",
				"value": led
			},
            {
				"name": "MOTION",
				"value": mot
			}
		]
	)
	client.publish(topic, data)
	time.sleep(1)
