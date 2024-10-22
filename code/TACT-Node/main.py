######################################## Declarartion for DL model
import sensor, image, lcd, time
import KPU as kpu
from machine import UART, SPI
import gc, sys
from fpioa_manager import fm
from Maix import freq, GPIO
from micropython import const
from XL1278 import *

input_size = (224, 224)
labels = ['handgun', 'rifle']
anchors = [6.94, 4.19, 6.94, 6.19, 6.94, 5.44, 6.94, 6.94, 6.94, 3.27]
thresh=0.85
nms_value=0.3
NodeID=1
counter=1
location='LNMIIT-Jaipur'
################# lora config ################
LORA_CS = const(21)# pin 2
LORA_SPI_SCK = const(22)#HS6 pin 3
LORA_SPI_MOSI = const(23)#HS7  pin 4
LORA_SPI_MISO = const(24)#HS8  pin 5
LORA_SPI_NUM = SPI.SPI_SOFT
LORA_SPI_FREQ_KHZ = const(10000)
##############################################

def sendLora(lora, threat, weapon):
    counter = 0
    print("LoRa Sender")
    #payload = ['Node Id {}'.format(NodeID),
        #'Threat Level {}'.format(threat),
        #'Weapon Type {}'.format(weapon),
        #'Latitude {}'.format("Latitude"),
        #'Longitude {}'.format("Longitude")
    #]
    payload = ['{}'.format(NodeID),
        '{}'.format(threat),
        '{}'.format(weapon),
        '{}'.format(location)
    ]
    payload_str = ', '.join(payload)
    lora.println(payload_str)
    print(payload)# Send the combined payload as a string
    counter=counter+1;
    print("Sending packet:\n{}".format(counter))

##################################
#######Declaration for WiFi#######
WIFI_SSID   = "LAPTOP"
WIFI_PASSWD = "12345678910"
addr        = ("172.22.103.24", 3456)
ADDR = ("172.22.103.24", 60003)
import socket
clock = time.clock()
lcd.init()
sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)
sensor.skip_frames(time = 2000)
##################################
##################################
def enable_esp32():
    from network_esp32 import wifi
    if wifi.isconnected() == False:
        for i in range(5):
            try:
                # Running within 3 seconds of power-up can cause an SD load error
                # wifi.reset(is_hard=False)
                wifi.reset(is_hard=True)
                print('try AT connect wifi...')
                wifi.connect(WIFI_SSID, WIFI_PASSWD)
                if wifi.isconnected():
                    break
            except Exception as e:
                print(e)
    print('network state:', wifi.isconnected(), wifi.ifconfig())

def lcd_show_except(e):
    import uio
    err_str = uio.StringIO()
    sys.print_exception(e, err_str)
    err_str = err_str.getvalue()
    img = image.Image(size=input_size)
    img.draw_string(0, 10, err_str, scale=1, color=(0xff,0x00,0x00))
    lcd.display(img)

class Comm:
    def __init__(self, uart):
        self.uart = uart

    def send_detect_result(self, objects, labels):
        msg = ""
        for obj in objects:
            pos = obj.rect()
            p = obj.value()
            idx = obj.classid()
            label = labels[idx]
            msg += "{}:{}:{}:{}:{}:{:.2f}:{}, ".format(pos[0], pos[1], pos[2], pos[3], idx, p, label)
        if msg:
            msg = msg[:-2] + "\n"
        self.uart.write(msg.encode())

def init_uart():
    fm.register(10, fm.fpioa.UART1_TX, force=True)
    fm.register(11, fm.fpioa.UART1_RX, force=True)

    uart = UART(UART.UART1, 115200, 8, 0, 0, timeout=1000, read_buf_len=256)
    return uart

def send_payload_over_socket(threat,weapon):
    sock1 = socket.socket()
    sock1.connect(ADDR)
    payload_list = ['{}'.format(NodeID),
           '{}'.format(threat),
           '{}'.format(weapon),
           '{}'.format(location)]
    sock1.settimeout(1)
    for data in payload_list:
        data_with_newline = data + '\n'
        # Send the data as bytes
        sock1.send(data_with_newline.encode('utf-8'))
        print("Sent: {data}")  # Print the data being sent
        #time.sleep(1)
    sock1.close()

def send_image_over_socket(img, clock):
    while True:
        try:
            sock = socket.socket()
            print(sock)
            sock.connect(addr)
            break
        except Exception as e:
            print("connect error:", e)
            sock.close()
            continue
    sock.settimeout(5)
    send_len, count, err = 0, 0, 0
    clock.tick()
    if err >=10:
        print("socket broken")
        return

    img = img.compress(quality=90)
    img_bytes = img.to_bytes()
    print("send len: ", len(img_bytes))
    packet_prescalar=2048
    try:
        block = int(len(img_bytes)/packet_prescalar)
        for i in range(block):
            send_len = sock.send(img_bytes[i*packet_prescalar:(i+1)*packet_prescalar])
        send_len2 = sock.send(img_bytes[block*packet_prescalar:])
        print("image confirmed sent")
        if send_len == 0:
            raise Exception("send fail")
    except OSError as e:
        print("exception")
        if e.args[0] == 128:
            print("connection closed")
            sys.print_exception(e)
    except Exception as e:
        print("send fail:", e)
        time.sleep(1)
        err += 1
        return
    count += 1
    print("send:", count)
    print("close now")
    sock.close()



def main(anchors, labels = None, model_addr="/sd/m.kmodel", sensor_window=input_size, lcd_rotation=0, sensor_hmirror=False, sensor_vflip=True):
    print("starting")
    #fm.register(LORA_CS, fm.fpioa.GPIOHS0, force=True) # CS
    #cs = GPIO(GPIO.GPIOHS0, GPIO.OUT)
    #spi1 = SPI(LORA_SPI_NUM, mode=SPI.MODE_MASTER, baudrate=LORA_SPI_FREQ_KHZ * 1000,
               #polarity=0, phase=0, bits=8, firstbit=SPI.MSB, sck=LORA_SPI_SCK, mosi=LORA_SPI_MOSI, miso = LORA_SPI_MISO)
    #lora = SX127x(spi=spi1, pin_ss=cs)
    #time.sleep_ms(100)
    #lora.init()
    sensor.reset()
    sensor.set_pixformat(sensor.RGB565)
    sensor.set_framesize(sensor.QVGA)
    sensor.set_windowing(sensor_window)
    sensor.set_hmirror(sensor_hmirror)
    sensor.set_vflip(sensor_vflip)
    sensor.run(1)
    lcd.init(type=1)
    lcd.rotation(lcd_rotation)
    lcd.clear(lcd.WHITE)

    if not labels:
        with open('labels.txt','r') as f:
            exec(f.read())
    if not labels:
        print("no labels.txt")
        img = image.Image(size=(320, 240))
        img.draw_string(90, 110, "no labels.txt", color=(255, 0, 0), scale=2)
        lcd.display(img)
        return 1
    try:
        img = image.Image("startup.jpg")
        lcd.display(img)
    except Exception:
        img = image.Image(size=(320, 240))
        img.draw_string(90, 110, "loading model...", color=(255, 255, 255), scale=2)
        lcd.display(img)

    uart = init_uart()
    comm = Comm(uart)

    try:
        a=0;
        task = None
        task = kpu.load(model_addr)
        kpu.init_yolo2(task, thresh, nms_value, 5, anchors) # threshold:[0,1], nms_value: [0, 1]
        while(True):
            if a==1:
                task = None
                task = kpu.load(model_addr)
                kpu.init_yolo2(task, thresh, nms_value, 5, anchors) # threshold:[0,1], nms_value: [0, 1]
                a=0;
            img = sensor.snapshot()
            img.rotation_corr(z_rotation=90)
            t = time.ticks_ms()
            objects = kpu.run_yolo2(task, img)
            if objects:
                for obj in objects:
                    pos = obj.rect()
                    img.draw_rectangle(pos)
                    img.draw_string(pos[0], pos[1], "%s : %.2f" %(labels[obj.classid()], obj.value()), scale=1, color=(255, 0, 0))
                    kpu.deinit(task)
                    img1=img
                    send_image_over_socket(img1, clock)
                    send_payload_over_socket(labels[obj.classid()],obj.value())
                    #sendLora(lora, labels[obj.classid()], obj.value())
                    print("cycle complete")
                    a=1;
                comm.send_detect_result(objects, labels)
            t = time.ticks_ms() - t
    except Exception as e:
        raise e
    finally:
        if not task is None:
            kpu.deinit(task)


if __name__ == "__main__":
    try:
        enable_esp32()
        # main(anchors = anchors, labels=labels, model_addr=0x300000, lcd_rotation=0)
        main(anchors = anchors, labels=labels, model_addr="/sd/model-152080.kmodel")
    except Exception as e:
        sys.print_exception(e)
        lcd_show_except(e)
    finally:
        gc.collect()
