from CubeSat import CubeSat
from time import sleep, time
import urequests
import json
import network

print("turning on...")
sat = CubeSat() # inicia a classe do satélite
sat.beep(freq=5000)
if sat.internet_mode: sat.wifi_connect(ssid="MAKE_CURSINHO", password="nossainternet") #conecta a rede wi-fi
sat.beep(freq=5000)
sat.mount_sd() # monta cartão microSD
print("sd mounted")
sat.beep(freq=5000)

# variáveis editáveis
server = "https://obsat.org.br/teste_post/envio.php" # servidor de envio dos dados via requisição POST
min_interval = 1 # segundos entre cada execução
exec_num = 0

while True:
    print("waiting execution... ")
    start_time = time()
    while((time()-start_time)<min_interval): pass # aguarda o intervalo entre as execuções
    sat.beep()
    exec_num+=1
    print(f"execução número {exec_num}")
    
    # captura dos dados de telemetria e payload
    telemetry = {
        'equipe': 33,
        'bateria': sat.get_battery_level(),
        'temperatura': sat.temperature(),
        'pressao': sat.pressure(),
        'giroscopio': sat.gyroscope(),
        'acelerometro': sat.acceleration(),
        'payload': {
            'umidade': sat.humidity(),
            'time': time(),
            'altitude': sat.altitude()

        },
    }
    telemetry['payload'].update(sat.get_air_quality()) # adiciona ao payload os dados dos gases
    json_telemetry = json.dumps(telemetry) # conversão para o padrão json
    print("json_telemetry:", json_telemetry)
    
    # salva no cartão microSD
    with open(f'/sd/telemetry.json', 'a+') as file:
        file.write(json_telemetry+"\n")
        print("saved on sd card")

    #envia os dados via wi-fi
    if sat.internet_mode:
        print("sending packet...")
        try:
            response = urequests.post(url=server, data=json_telemetry)
            response.close()
            print(f"{response.status_code} packet sent to {server}")
        except Exception as e:
            print("something bad happened:", e)
            sta_if = network.WLAN(network.STA_IF)
            print(f"sta_if.isconnected(): {sta_if.isconnected()}")
            for i in range(10): sat.beep(); sleep(0.1)
        except KeyboardInterrupt as e:
            raise e
    else:
        print(f"internet mode {str(sat.internet_mode).upper()}, skipping...")

    sat.beep(freq=2000)
    print("="*120)

