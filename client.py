# client.py - Chat Client with Command Line Port Support
import socket
import threading
import sys

class ChatClient:
    def __init__(self, host='localhost', port=5000):
        self.host = host
        self.port = port
        self.socket = None
        self.running = True

    def receive_messages(self):
        """Continuously receive and display messages from the server"""
        while self.running:
            try:
                message = self.socket.recv(1024).decode('utf-8')
                if not message:
                    break
                print(f"\n{message}")
                print("💬 You: ", end="", flush=True)
            except:
                break
        
        if self.running:
            print("\n🔴 Disconnected from server")
            self.running = False

    def connect(self):
        """Connect to the chat server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            
            # Start the receiving thread
            receive_thread = threading.Thread(target=self.receive_messages, daemon=True)
            receive_thread.start()
            
            print("=" * 50)
            print("💬 CONNECTED TO CHAT SERVER!")
            print(f"📡 Server: {self.host}:{self.port}")
            print("📝 Type /help for available commands")
            print("🚪 Type /quit to exit")
            print("=" * 50)
            
            return True
            
        except ConnectionRefusedError:
            print(f"❌ Could not connect to {self.host}:{self.port}")
            print("   Make sure the server is running.")
            return False
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False

    def send_message(self, message):
        """Send a message to the server"""
        try:
            self.socket.send(message.encode('utf-8'))
        except:
            print("❌ Failed to send message")
            self.running = False

    def run(self):
        """Main client loop"""
        if not self.connect():
            return
        
        while self.running:
            try:
                message = input("💬 You: ")
                if not message:
                    continue
                    
                if message == '/quit':
                    self.send_message(message)
                    self.running = False
                    break
                
                self.send_message(message)
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                self.running = False
                break
            except:
                continue
        
        # Clean up
        if self.socket:
            self.socket.close()
        print("👋 Disconnected from chat")

def show_usage():
    """Display usage information"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║  💬 CHATGROUP CLIENT                                       ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  USAGE:                                                      ║
║    python3 client.py [HOST] [PORT]                          ║
║                                                              ║
║  EXAMPLES:                                                   ║
║    python3 client.py                 # localhost:5000       ║
║    python3 client.py 192.168.1.100   # Connect to server    ║
║    python3 client.py 192.168.1.100 5001                     ║
║                                                              ║
║  DEFAULT HOST: localhost                                    ║
║  DEFAULT PORT: 5000                                         ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)

if __name__ == "__main__":
    # Parse command line arguments
    host = 'localhost'
    port = 5000
    
    if len(sys.argv) > 1:
        if sys.argv[1] in ['--help', '-h']:
            show_usage()
            sys.exit(0)
        host = sys.argv[1]
        
    if len(sys.argv) > 2:
        try:
            port = int(sys.argv[2])
            if port < 1 or port > 65535:
                print("❌ Port must be between 1 and 65535")
                show_usage()
                sys.exit(1)
        except ValueError:
            print("❌ Invalid port number. Please enter a number.")
            show_usage()
            sys.exit(1)
    
    client = ChatClient(host, port)
    client.run()
