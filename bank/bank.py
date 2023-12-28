#!/usr/bin/env python
from socketserver import ThreadingUDPServer, ThreadingTCPServer, BaseRequestHandler
import threading, 	string

# Datos de servidores
bankTCP_address = ("0.0.0.0", 9000)               # Dirección y puerto TCP del servidor Bank

bankUDP_address = ("bank_container", 3459)              # Dirección y puerto UDP del servidor Bank
liquorStoreUDP_address = ("liquorstore_container", 3666)       # Dirección y puerto UDP del servidor LiquorStore

class BankUDPHandler(BaseRequestHandler):
    accounts = {
        "1234": {"nombre": "usuario1", "contraseña": "pass1", "saldo": 100},
        "5678": {"nombre": "usuario2", "contraseña": "pass2", "saldo": 100},
        "9012": {"nombre": "usuario3", "contraseña": "pass3", "saldo": 100},
    }
    def	cifradoUDP(self, text,	n):
	 #	alphabet	"abcdefghijklmnopqrstuvwxyz"	
        intab	=	string.ascii_lowercase	
        #	alphabet	shifted	by	n	positions
        outtab	=	intab[n	% 26:] +	intab[:n	% 26]	 	
    #	translation	made	b/w	patterns
        trantab	=	str.maketrans(intab,	outtab)		
    #	text	is	shifted	to	right	
        return	text.translate(trantab)

    def verificarSaldo(self, usuario, contraseña, costo):
        # Verificar las credenciales del usuario
        if usuario in self.accounts and contraseña == self.accounts[usuario]["contraseña"]:
            saldo_disponible = self.accounts[usuario]["saldo"]
            print(f"Saldo disponible para {usuario}: {saldo_disponible}")
            print(f"Monto a descontar para la compra: {costo}")
            if saldo_disponible >= costo:
                # Si el usuario tiene saldo suficiente
                self.accounts[usuario]["saldo"] -= costo  # Deduct the cost from the user's balance
                return "OK"
            else:
                return "Saldo insuficiente"
        else:
            return "Credenciales invalidas"
        
    def handle(self):
        data, conn = self.request  # Recibir datos de LIQUOR-STORE
        print(data)
        #decodificar data
        data_decodificada = self.cifradoUDP(data.decode(),-3)
        print(data_decodificada)

        # Almacenar datos entrantes
        decoded_data = data_decodificada.strip().split()  # Obtener el socket sin cifrar


        
        if len(decoded_data) >= 3:
            usuario = decoded_data[0]
            contraseña = decoded_data[1]
            costo = int(decoded_data[2])                                # Convertir a entero para comparaciones
            response = self.verificarSaldo(usuario, contraseña, costo)
            print(response) 
            conn.sendto(response.encode(), liquorStoreUDP_address)      # Responder a LiquorStore
        elif len(decoded_data) == 1:
            confirmacion = decoded_data[0]
            print(confirmacion)
            print("Compra realizada!")

class BankTCPHandler(BaseRequestHandler):
    def receive_fixed_length(self, length):
        data = self.request.recv(length).decode().strip()
        return data

    def handle(self):
        try:
            # Receive user details
            self.request.sendall("Ingrese el numero de la cuenta: \r\n".encode())
            user_number = self.receive_fixed_length(1024)

            self.request.sendall("Ingrese la contraseña: \r\n".encode())
            contraseña = self.receive_fixed_length(1024)

            if user_number in BankUDPHandler.accounts and contraseña == BankUDPHandler.accounts[user_number]["contraseña"]:

                while True:
                    # Display menu options
                    menu = "1. Consultar Saldo\n2.Consignar Saldo\n3. Retirar\n4. Salir\nSeleccione una opción (1/2/3/4): \r\n"
                    self.request.sendall(menu.encode())

                    # Receive user choice
                    choice = self.receive_fixed_length(1024)

                    if choice == '1':
                        # Verificar nombre, número de cuenta y contraseña posterior mostrar saldo
                        self.request.sendall(f"Ingrese la contraseña para el numero de cuenta {user_number}: ".encode())
                        user_password = self.receive_fixed_length(1024)

                        if user_number in BankUDPHandler.accounts and user_password == BankUDPHandler.accounts[user_number]["contraseña"]:
                            saldo_disponible = BankUDPHandler.accounts[user_number]["saldo"]
                            nombre_usuario = BankUDPHandler.accounts[user_number]["nombre"]
                            message = f"Saldo disponible para {nombre_usuario}, cuenta {user_number}: {saldo_disponible} \r\n"
                        else:
                            message = "Credenciales incorrectas \r\n"
                    elif choice == '2':
                        #Ingresar el monta a consignar
                        self.request.sendall(f"Ingrese la cantidad a consignar para la cuenta {user_number}: ".encode())
                        deposit_amount = int(self.receive_fixed_length(1024))
                        
                        self.request.sendall(f"Desea confirmar valor de  {deposit_amount} y/n: \r\n".encode())
                        confirmation = self.receive_fixed_length(1024)

                        if confirmation == "y":                                    
                            BankUDPHandler.accounts[user_number]["saldo"] += deposit_amount
                            message = f"Consignación exitosa. Nuevo saldo para la cuenta {user_number}: {BankUDPHandler.accounts[user_number]['saldo']} \r\n"
                        elif confirmation == "n":
                            message = f"Consignación cancelada. El saldo para la cuenta {user_number}: {BankUDPHandler.accounts[user_number]['saldo']} \r\n"
                        else:
                            message = f"Entrada no válida. Debe ingresar 'y' o 'n' \r\n "                   
                    elif choice == '3':
                        #Ingresar el monta a retirar
                        self.request.sendall(f"Ingrese la cantidad a retirar para la cuenta {user_number}: ".encode())
                        deposit_amount = int(self.receive_fixed_length(1024))
                        saldo = BankUDPHandler.accounts[user_number]["saldo"]
                        total_deposit = saldo - deposit_amount
                        if total_deposit > 0 :
                            self.request.sendall(f"Desea confirmar valor de  {deposit_amount} y/n: \r\n".encode())
                            confirmation = self.receive_fixed_length(1024)
                            if confirmation == "y":                                          
                                saldo -= deposit_amount
                                BankUDPHandler.accounts[user_number]["saldo"] -= deposit_amount
                                message = f"Se ha retirado {deposit_amount}. Tu saldo actual  para la cuenta {user_number}: {saldo} \r\n"
                            elif confirmation == "n":
                                message = f"Operacion cancelada. El saldo para la cuenta {user_number} es {saldo} \r\n"
                            else:
                                message = f"Entrada no válida. Debe ingresar 'y' o 'n' \r\n "
                        else:
                            message = f"Tu saldo es insuficiente"                
                    elif choice == '4':
                        # Salir del bucle
                        message = "Gracias por utilizar nuestros servicios. Hasta luego.\r\n"
                        self.request.sendall(message.encode())
                        break
                    else:
                        message = "Opción no válida"

                    self.request.sendall(message.encode())
            else:
                message = "Usuario o contraseña incorrectos. Inténtelo nuevamente.\r\n"
                self.request.sendall(message.encode())

        except Exception as e:
            print(f"Error during handling: {e}")

try:
    # Inicializar servidor UDP para Bank
    bank_udp_server = ThreadingUDPServer(bankUDP_address, BankUDPHandler)
    bank_udp_thread = threading.Thread(target=bank_udp_server.serve_forever)

    # Inicializar servidor TCP para Bank
    bank_tcp_server = ThreadingTCPServer(bankTCP_address, BankTCPHandler)
    bank_tcp_thread = threading.Thread(target=bank_tcp_server.serve_forever)

    # Print server addresses before starting
    print(f"BANK iniciará por el puerto UDP: {bankUDP_address[1]}")
    print(f"BANK iniciará por el puerto TCP: {bankTCP_address[1]}")

    # Start the server threads
    bank_udp_thread.start()
    bank_tcp_thread.start()

    # Wait for the server threads to finish
    bank_udp_thread.join()
    bank_tcp_thread.join()

except Exception as error:
    print(f"BANK no pudo iniciarse: {error}")
