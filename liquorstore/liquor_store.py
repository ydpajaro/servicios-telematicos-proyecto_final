#!/usr/bin/env python
from socketserver import ThreadingTCPServer, ThreadingUDPServer, BaseRequestHandler
from threading import Thread
from socket import *
import string

# Datos simulados de inventario de licores
inventory = {
    1: {"nombre": "Aguardiente", "origen": "CO", "unidades": 10, "precio": 10},
    2: {"nombre": "Rum", "origen": "BB", "unidades": 8, "precio": 25},
    3: {"nombre": "Whisky", "origen": "SC", "unidades": 5, "precio": 30},
    4: {"nombre": "Gin", "origen": "UK", "unidades": 4, "precio": 20},
    5: {"nombre": "Vodka", "origen": "RU", "unidades": 5, "precio": 15},
}
responses = []                                  # Lista compartida para respuestas a clientes

# PUERTOS USADOS
# CLIENTES
liquorStoreTCP_address = ("0.0.0.0", 8001)    # TCP LiquorStore
# BANK
liquorStoreUDP_address = ("liquorstore_container", 3666)    # UDP LiquorStore
bankUDP_adress = ("bank_container", 3459)            # UDP Bank


class LiquorStore(BaseRequestHandler):
    def menu(self, usuariosConectados):
            mensaje = f"Usuarios conectados: ({usuariosConectados})\n"
            mensaje += f"\nMENU PRINCIPAL:\n"
            mensaje += f"1. Ver licores disponibles.\n"
            mensaje += f"2. Comprar un licor.\n"
            mensaje += f"3. Salir.\n"
            mensaje += f"4. Actualizar menu principal.\n"
            self.request.send(mensaje.encode())
    def obtener_listado_licores(self):
        response = "\nListado de Licores:\n"
        for codigo, detalles in inventory.items():
            response += f"\nCódigo: {codigo}\n"
            response += f"Licor: {detalles['nombre']}\n"
            response += f"Procedencia: {detalles['origen']}\n"
            response += f"Unidades disponibles: {detalles['unidades']}\n"
            response += f"Costo por unidad: {detalles['precio']}\n"
        return response
    
    def procesarCompra(self, liquor_code,quantity):
        licor = inventory.get(int(liquor_code))
        if licor:

            self.request.sendall(b"Estas intentado realizar una compra, por favor ingresar en tu banco.\r\n")
            self.request.sendall(b"Numero de cuenta:")
            username = self.request.recv(1024).decode().strip()
            self.request.sendall(b"Ahora ingresa el password:")
            password = self.request.recv(1024).decode().strip()
            costo = licor["precio"] * quantity
            user_credentials = f"{username} {password} {costo}"
            return user_credentials
        
    def realizarCompra(self, licor, quantity):
        costo = licor["precio"] * quantity

        # Verificar si hay suficientes unidades disponibles
        if licor["unidades"] >= quantity:
            # Realizar la compra y decrementar unidades
            licor["unidades"] -= quantity
            response = f"Compra exitosa. Se han comprado {quantity} unidades de {licor['nombre']} por un total de {costo}.\n"
        else:
            response = f"No hay suficientes unidades disponibles de {licor['nombre']} para la cantidad solicitada.\n"

        return response
        
    def enviar_a_Banco(self, mensaje):
        # Enviar al banco
        bank_socket = socket(AF_INET, SOCK_DGRAM)
        bank_socket.sendto(mensaje.encode(), bankUDP_adress)

    def responderCliente(self):
        while True:
            if responses:
                response = responses.pop(0)
                for socket in self.server.sockets:
                    socket.send(response.encode())
    def	cifradoUDP(self, text,	n):
	 #	alphabet	"abcdefghijklmnopqrstuvwxyz"	
        intab	=	string.ascii_lowercase	
        #	alphabet	shifted	by	n	positions
        outtab	=	intab[n	% 26:] +	intab[:n	% 26]	 	
    #	translation	made	b/w	patterns
        trantab	=	str.maketrans(intab,	outtab)		
    #	text	is	shifted	to	right	
        return	text.translate(trantab)

    def handle(self):
        self.server.sockets.append(self.request)
        self.server.usuariosConectados += 1
        self.request.send(b"\nBIENVENIDO A LIQUOR-STORE.\r\n")
        
        # Iniciar hilo para enviar respuestas a los clientes
        response_thread = Thread(target=self.responderCliente)
        response_thread.start()
        
        while True:
            self.menu(self.server.usuariosConectados)
            data = self.request.recv(1024)
            decoded_data = data.decode().split()
            command = decoded_data[0]


            if command == "1":
                # Imprimir la lista de licores organizada
                #response = "\r\n".join([f"{key}: {value}" for key, value in inventory.items()]) + "\r\n"
                message = self.obtener_listado_licores()
                self.request.sendall(message.encode())
            elif command == "2":
                # Comprar
                self.request.sendall("Ingrese el codigo del licor que desea comprar.\r\n".encode())
                liquor_code = self.request.recv(1024).decode().strip()
                if liquor_code:
                    self.request.sendall("Ingrese la cantidad de licor que desea comprar.\r\n".encode())
                    liquor_amount = int(self.request.recv(1024).decode().strip())
                    if liquor_amount >0:
                        user_credentials = self.procesarCompra(liquor_code,liquor_amount)             # Hacer una compra
                        user_cifrado = self.cifradoUDP(user_credentials,3)
                        print(user_cifrado)
                        self.enviar_a_Banco(user_cifrado)                           # Enviar la informacion al banco
                        confirmacion = self.request.recv(1024).decode().strip().lower() # Esperar al cliente confirmar compra

                        if confirmacion == 'y':
                            # Realizar la compra y enviar confirmación al banco
                            response = self.realizarCompra(inventory.get(int(liquor_code)), liquor_amount)
                            self.request.sendall(response.encode())

                            #self.request.sendall("Compra realizada.\r\n".encode())
                            self.enviar_a_Banco(confirmacion)   
                        elif confirmacion == 'n': # Enviar la confirmación al banco
                            message = "Se cancela la compra" 
                        else:
                            print("Entrada no válida. Debe ingresar 'y' o 'n'.")
                            message = "Entrada no válida. Debe ingresar 'y' o 'n'"
            elif command == "3":
                # Salir
                self.server.usuariosConectados -= 1                                 # Decrementar usuario que abandona
                self.server.sockets.remove(self.request)
                break
            elif command == "4":
                self.menu(self.server.usuariosConectados)
            else:
                self.request.sendall("Comando invalido.\r\n".encode())
                self.menu(self.server.usuariosConectados)
        self.request.close()

class respBankHandler(BaseRequestHandler):
    
        
    def handle(self):
        data, conn = self.request
        resp_bank = data.decode()
        print(resp_bank.upper())
        if resp_bank == "OK":           
            responses.append("Desea confirmar la compra? y/n\r\n")                     
        elif resp_bank == "Saldo insuficiente":
            responses.append("Usted no posee saldo suficiente para hacer esta compra.\r\n") 
        elif resp_bank == "Credenciales invalidas":
            responses.append("Error de autenticacion, intente de nuevo.\r\n")
        else:
            responses.append("Error al procesar respuesta con su banco, intente nuevamente.\r\n")

try:
    # Inicializar servidor TCP
    liquor_server1 = ThreadingTCPServer(liquorStoreTCP_address, LiquorStore)
    liquor_server1.usuariosConectados = 0    # Manejar usuarios conectados
    liquor_server1.sockets = []              # Lista para almacenar los sockets de los clientes
    liquorStore_TCP = Thread(target=liquor_server1.serve_forever)
    liquorStore_TCP.start()
    print(f"LIQUOR-STORE inició en puerto TCP {liquorStoreTCP_address[1]}")
except Exception as error:
    print(f"LIQUOR-STORE no pudo iniciarse en puerto TCP {liquorStoreTCP_address[1]}: {error}")

try:
    # Inicializar servidor UDP
    liquor_server2 = ThreadingUDPServer(liquorStoreUDP_address, respBankHandler)
    liquorStore_UDP = Thread(target=liquor_server2.serve_forever)
    liquorStore_UDP.start()
    print(f"LIQUOR-STORE inició en puerto UDP {liquorStoreUDP_address[1]}")
except Exception as error:
    print(f"LIQUOR-STORE no pudo iniciarse en puerto UDP {liquorStoreUDP_address[1]}: {error}")
