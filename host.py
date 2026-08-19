# host.py - Complete Chat Server with Command Line Port Support
import socket
import threading
import sys
import signal

class ChatServer:
    def __init__(self, host='0.0.0.0', port=5000):
        self.host = host
        self.port = port
        self.clients = []  # List to store all connected clients
        self.names = {}    # Dictionary to store client names {socket: name}
        self.server_socket = None
        self.running = True
        self.host_name = "👑 Host"

    def broadcast(self, message, sender_socket=None):
        """Send a message to all connected clients except the sender"""
        for client in self.clients:
            if client != sender_socket:
                try:
                    client.send(message.encode('utf-8'))
                except:
                    self.remove_client(client)

    def broadcast_to_all(self, message):
        """Send a message to ALL connected clients"""
        for client in self.clients:
            try:
                client.send(message.encode('utf-8'))
            except:
                self.remove_client(client)

    def remove_client(self, client_socket):
        """Remove a client from the server"""
        if client_socket in self.clients:
            self.clients.remove(client_socket)
            if client_socket in self.names:
                name = self.names[client_socket]
                del self.names[client_socket]
                self.broadcast(f"🔴 {name} has left the chat.", client_socket)
                print(f"🔴 {name} disconnected")
            client_socket.close()

    def handle_client(self, client_socket, address):
        """Handle communication with a single client"""
        print(f"✅ New connection from {address}")
        
        # Ask for name
        client_socket.send("Enter your name: ".encode('utf-8'))
        name = client_socket.recv(1024).decode('utf-8').strip()
        
        # Handle duplicate names
        while name in self.names.values() or name == self.host_name:
            client_socket.send("Name already taken! Enter another name: ".encode('utf-8'))
            name = client_socket.recv(1024).decode('utf-8').strip()
        
        # Store client name
        self.names[client_socket] = name
        self.clients.append(client_socket)
        
        # Welcome message
        client_socket.send(f"✅ Welcome {name}! Type /help for commands.\n".encode('utf-8'))
        
        # Broadcast join message
        self.broadcast(f"🟢 {name} has joined the chat!", client_socket)
        print(f"🟢 {name} joined the chat")
        
        # Send current users list
        user_list = ", ".join(self.names.values())
        client_socket.send(f"👥 Online users: {user_list}\n".encode('utf-8'))
        
        # Main message loop
        while self.running:
            try:
                message = client_socket.recv(1024).decode('utf-8').strip()
                if not message:
                    break
                
                # Handle commands
                if message.startswith('/'):
                    self.handle_command(client_socket, message)
                else:
                    # Broadcast the message to everyone
                    self.broadcast(f"💬 {name}: {message}", client_socket)
                    print(f"💬 {name}: {message}")
                    
            except:
                break
        
        # Client disconnected
        self.remove_client(client_socket)

    def handle_command(self, client_socket, command):
        """Handle special commands from clients"""
        name = self.names.get(client_socket, "Unknown")
        
        if command == '/help':
            help_text = """
📚 Available Commands:
  /help     - Show this help message
  /users    - List all online users
  /quit     - Leave the chat
  /msg NAME MESSAGE - Send private message
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
                # Find target client
                for sock, name in self.names.items():
                    if name == target_name:
                        sock.send(f"📩 [Private] {name}: {private_msg}".encode('utf-8'))
                        client_socket.send(f"📤 [Private] to {target_name}: {private_msg}".encode('utf-8'))
                        return
                client_socket.send(f"❌ User '{target_name}' not found.".encode('utf-8'))
            else:
                client_socket.send("❌ Usage: /msg NAME MESSAGE".encode('utf-8'))
                
        elif command == '/quit':
            self.remove_client(client_socket)
            
        else:
            client_socket.send(f"❌ Unknown command: {command}. Type /help for commands.".encode('utf-8'))

    def host_chat_loop(self):
        """Allow the host to send messages from the server terminal"""
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
                
                # If it's a regular message, broadcast it
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
        """Start the chat server with host chat capability"""
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
            
            # Start the host chat loop in a separate thread
            host_thread = threading.Thread(target=self.host_chat_loop, daemon=True)
            host_thread.start()
            
            # Main server loop
            while self.running:
                try:
                    client_socket, address = self.server_socket.accept()
                    # Handle each client in a new thread
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
        """Stop the server and clean up"""
        self.running = False
        # Close all client connections
        for client in self.clients[:]:
            try:
                client.close()
            except:
                pass
        if self.server_socket:
            self.server_socket.close()
        print("✅ Server stopped")

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\n🛑 Shutting down server...")
    sys.exit(0)

def show_usage():
    """Display usage information"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║  🖥️  CHATGROUP HOST SERVER                                 ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  USAGE:                                                      ║
║    python3 host.py [PORT]                                   ║
║                                                              ║
║  EXAMPLES:                                                   ║
║    python3 host.py          # Start on default port 5000   ║
║    python3 host.py 5001     # Start on port 5001           ║
║    python3 host.py 8080     # Start on port 8080           ║
║                                                              ║
║  DEFAULT PORT: 5000                                         ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)

if __name__ == "__main__":
    # Set up signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    # Parse command line arguments
    port = 5000  # Default port
    
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
            if port < 1 or port > 65535:
                print("❌ Port must be between 1 and 65535")
                show_usage()
                sys.exit(1)
        except ValueError:
            print("❌ Invalid port number. Please enter a number.")
            show_usage()
            sys.exit(1)
    
    # Show usage if --help or -h is passed
    if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h']:
        show_usage()
        sys.exit(0)
    
    # Get local IP address
    def get_local_ip():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return '127.0.0.1'
    
    local_ip = get_local_ip()
    
    print("\n" + "=" * 60)
    print(f"🚀 Starting Chat Server on port {port}")
    print(f"📡 Local IP: {local_ip}")
    print(f"🔗 Connect with: python3 client.py {local_ip} {port}")
    print("=" * 60 + "\n")
    
    # Create and start server
    server = ChatServer(host='0.0.0.0', port=port)
    
    try:
        server.start_server()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)
