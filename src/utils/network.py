import socket
import struct
import os

class FileSender:
    def __init__(self, host, port=5001):
        self.host = host
        self.port = port
        self.sock = None

    def connect(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.host, self.port))
            print(f"Connected to {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False

    def send_file(self, filepath):
        if not self.sock:
            if not self.connect():
                return False

        try:
            filename = os.path.basename(filepath)
            filesize = os.path.getsize(filepath)

            # Protocol: 
            # 1. Filename length (4 bytes)
            # 2. Filename (N bytes)
            # 3. File size (8 bytes)
            # 4. File data (filesize bytes)

            encoded_filename = filename.encode('utf-8')
            self.sock.sendall(struct.pack('!I', len(encoded_filename)))
            self.sock.sendall(encoded_filename)
            self.sock.sendall(struct.pack('!Q', filesize))

            with open(filepath, 'rb') as f:
                while True:
                    data = f.read(4096)
                    if not data:
                        break
                    self.sock.sendall(data)
            
            print(f"Sent {filename} successfully.")
            return True
        except Exception as e:
            print(f"Error sending file: {e}")
            return False
        finally:
            self.close()

    def close(self):
        if self.sock:
            self.sock.close()
            self.sock = None

class FileReceiver:
    def __init__(self, port=5001, save_dir='received_files'):
        self.port = port
        self.save_dir = save_dir
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(('0.0.0.0', self.port))
        self.sock.listen(1)
        self.sock.settimeout(0.1)  # Non-blocking accept for the loop
        print(f"Listening on port {self.port}...")

    def accept_and_receive(self):
        try:
            conn, addr = self.sock.accept()
            print(f"Connection from {addr}")
            
            # Read filename length
            name_len_data = self.recv_all(conn, 4)
            if not name_len_data: return None
            name_len = struct.unpack('!I', name_len_data)[0]

            # Read filename
            filename_data = self.recv_all(conn, name_len)
            filename = filename_data.decode('utf-8')

            # Read filesize
            filesize_data = self.recv_all(conn, 8)
            filesize = struct.unpack('!Q', filesize_data)[0]

            # Read file
            save_path = os.path.join(self.save_dir, filename)
            received = 0
            with open(save_path, 'wb') as f:
                while received < filesize:
                    chunk_size = min(4096, filesize - received)
                    data = self.recv_all(conn, chunk_size)
                    if not data:
                        break
                    f.write(data)
                    received += len(data)
            
            conn.close()
            print(f"Received file: {save_path}")
            return save_path
        except socket.timeout:
            return None
        except Exception as e:
            print(f"Error receiving: {e}")
            return None

    def recv_all(self, sock, count):
        buf = b''
        while count:
            newbuf = sock.recv(count)
            if not newbuf: return None
            buf += newbuf
            count -= len(newbuf)
        return buf
