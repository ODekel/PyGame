import socket


HEADER_SIZE = 8


class Sock(socket.socket):
    """Class that is an extension of socket.socket."""
    def __init__(self, *args, **kwargs):
        """Create a new Sock object."""
        super(Sock, self).__init__(*args, **kwargs)

    @classmethod
    def copy(cls, sock):
        """Create a Sock object using an existing socket.socket object."""
        copy = cls(sock.family, sock.type, sock.proto, _sock=sock.dup())
        copy.settimeout(sock.gettimeout())
        return copy

    def accept(self):
        """Behaves like the socket.socket's accept method, but returns a Sock object instead."""
        default_socket, addr = socket.socket.accept(self)
        sock = Sock.copy(default_socket)
        default_socket.close()
        return sock, addr

    def recv_by_size(self):
        """Receives by size (with a preprogrammed header size).
        The other side can use send_by_size to send the data."""
        str_size = ""
        str_size += self.recv(HEADER_SIZE)
        if str_size == "":
            return ""

        while len(str_size) < HEADER_SIZE:
            str_size += self.recv(HEADER_SIZE - len(str_size))
        size = int(str_size)

        data = ""
        while len(data) < size:
            data += self.recv(size - len(data))
        return data

    def send_by_size(self, s):
        """Sends by size (with a preprogrammed header size).
        The other side can use recv_by_size to receive the data."""
        self.sendall(str(len(s)).zfill(HEADER_SIZE))
        self.sendall(s)
