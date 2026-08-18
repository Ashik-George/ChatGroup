import socket
import threading
import time
import sys

class ChatServer:
    def __init__(self, host='0.0.0.0', port=5000):
        self.host = host
        self.port = port
        self.clients = []
        self.names = {}
        self.server_socket = None
        self.running = True
        self.host_name = "👑 Host"

    def broadcast(self, message, sender_socket=None):
        for client in self.clients:
            if client != sender_socket:
                try:
                    client.send(message.encode('utf-8'))
                except:
                    self.remove_client(client)

    def broadcast_to_all(self, message):
        for client in self.clients:
            try:
                client.send(message.encode('utf-8'))
            except:
                self.remove_client(client)

    def remove_client(self, client_socket):
        if client_socket in self.clients:
            self.clients.remove(client_socket)
            if client_socket in self.names:
                name = self.names[client_socket]
                del self.names[client_socket]
                self.broadcast(f"🔴 {name} has left the chat.", client_socket)
                print(f"🔴 {name} disconnected")
            client_socket.close()

    def handle_client(self, client_socket, address):
        print(f"✅ New connection from {address}")
        
        client_socket.send("Enter your name: ".encode('utf-8'))
        name = client_socket.recv(1024).decode('utf-8').strip()
        
        while name in self.names.values() or name == self.host_name:
            client_socket.send("Name already taken! Enter another name: ".encode('utf-8'))
            name = client_socket.recv(1024).decode('utf-8').strip()
        
        self.names[client_socket] = name
        self.clients.append(client_socket)
        
        client_socket.send(f"✅ Welcome {name}! Type /help for commands.\n".encode('utf-8'))
        self.broadcast(f"🟢 {name} has joined the chat!", client_socket)
        print(f"🟢 {name} joined the chat")
        
        user_list = ", ".join(self.names.values())
        client_socket.send(f"👥 Online users: {user_list}\n".encode('utf-8'))
        
        while self.running:
            try:
                message = client_socket.recv(1024).decode('utf-8').strip()
                if not message:
                    break
                
                if message.startswith('/'):
                    self.handle_command(client_socket, message)
                else:
                    self.broadcast(f"💬 {name}: {message}", client_socket)
                    print(f"💬 {name}: {message}")
                    
            except:
                break
        
        self.remove_client(client_socket)

    def handle_command(self, client_socket, command):
        name = self.names.get(client_socket, "Unknown")
        
        if command == '/help':
            help_text = """
📚 Available Commands:
  /help     - Show this help message
  /users    - List all online users
  /quit     - Leave the chat
  /msg NAME MESSAGE - Send private message
  /kick NAME - Kick a user (Host only)
"""
            client_socket.send(help_text.encode('utf-8'))
            
        elif command == '/users':
            user_list = "👥 Online users:\n"
            for user in self.names.values():
                user_list += f"  • {user}\n"
            client_socket.send(user_list.encode('utf-8'))
            
        elif command.startswith('/msg '):
            parts = command[5:].split(' ', 1)
            if len(parts) == 2:
                target_name, private_msg = parts
                for sock, name in self.names.items():
                    if name == target_name:
                        sock.send(f"📩 [Private] {name}: {private_msg}".encode('utf-8'))
                        client_socket.send(f"📤 [Private] to {target_name}: {private_msg}".encode('utf-8'))
                        return
                client_socket.send(f"❌ User '{target_name}' not found.".encode('utf-8'))
            else:
                client_socket.send("❌ Usage: /msg NAME MESSAGE".encode('utf-8'))
                
        elif command.startswith('/kick '):
            target_name = command[6:].strip()
            for sock, name in list(self.names.items()):
                if name == target_name:
                    sock.send("🚫 You have been kicked by the host.".encode('utf-8'))
                    self.remove_client(sock)
                    self.broadcast(f"👢 {target_name} was kicked by the host.")
                    return
            client_socket.send(f"❌ User '{target_name}' not found.".encode('utf-8'))
                
        elif command == '/quit':
            self.remove_client(client_socket)
            
        else:
            client_socket.send(f"❌ Unknown command: {command}. Type /help for commands.".encode('utf-8'))

    def host_chat_loop(self):
        print("\n💬 You can now chat as the Host!")
        print("   Type your messages and press Enter to broadcast")
        print("   Type '/quit' to stop the server")
        print("   Type '/help' for host commands")
        print("=" * 50)
        
        while self.running:
            try:
                message = input()
                if not message:
                    continue
                
                if message == '/quit':
                    print("🛑 Shutting down server...")
                    self.running = False
                    break
                    
                elif message == '/help':
                    print("""
📚 Host Commands:
  /help     - Show this help
  /users    - List all online users
  /kick NAME - Kick a user
  /msg NAME MESSAGE - Send private message
  /quit     - Stop the server
""")
                    continue
                    
                elif message.startswith('/msg '):
                    parts = message[5:].split(' ', 1)
                    if len(parts) == 2:
                        target_name, private_msg = parts
                        found = False
                        for sock, name in self.names.items():
                            if name == target_name:
                                sock.send(f"📩 [Private] {self.host_name}: {private_msg}".encode('utf-8'))
                                print(f"📤 [Private] to {target_name}: {private_msg}")
                                found = True
                                break
                        if not found:
                            print(f"❌ User '{target_name}' not found.")
                    else:
                        print("❌ Usage: /msg NAME MESSAGE")
                    continue
                    
                elif message.startswith('/kick '):
                    target_name = message[6:].strip()
                    for sock, name in list(self.names.items()):
                        if name == target_name:
                            sock.send("🚫 You have been kicked by the host.".encode('utf-8'))
                            self.remove_client(sock)
                            self.broadcast(f"👢 {target_name} was kicked by the host.")
                            print(f"👢 Kicked {target_name}")
                            break
                    else:
                        print(f"❌ User '{target_name}' not found.")
                    continue
                    
                elif message == '/users':
                    user_list = "👥 Online users:\n"
                    for user in self.names.values():
                        user_list += f"  • {user}\n"
                    print(user_list)
                    continue
                
                if self.clients:
                    self.broadcast_to_all(f"💬 {self.host_name}: {message}")
                    print(f"💬 {self.host_name}: {message}")
                else:
                    print("⚠️ No clients connected. Your message was not sent.")
                    
            except KeyboardInterrupt:
                print("\n🛑 Shutting down...")
                self.running = False
                break
            except Exception as e:
                print(f"⚠️ Error: {e}")

    def start_server(self):
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(10)
            
            print("=" * 50)
            print("🖥️  CHAT SERVER STARTED!")
            print(f"📡 Listening on {self.host}:{self.port}")
            print(f"👑 Your name: {self.host_name}")
            print("💡 You can chat from this terminal too!")
            print("💡 Press Ctrl+C to stop the server")
            print("=" * 50)
            
            host_thread = threading.Thread(target=self.host_chat_loop, daemon=True)
            host_thread.start()
            
            while self.running:
                try:
                    client_socket, address = self.server_socket.accept()
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, address),
                        daemon=True
                    )
                    client_thread.start()
                    
                except Exception as e:
                    if self.running:
                        print(f"⚠️ Error accepting connection: {e}")
                    
        except Exception as e:
            print(f"❌ Failed to start server: {e}")
        finally:
            self.stop_server()

    def stop_server(self):
        self.running = False
        for client in self.clients[:]:
            try:
                client.close()
            except:
                pass
        if self.server_socket:
            self.server_socket.close()
        print("✅ Server stopped")

if __name__ == "__main__":
    server = ChatServer()
    try:
        server.start_server()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")