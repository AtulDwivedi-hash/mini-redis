import selectors
import socket
from resp import (
    parse_resp_array,
    serialize_bulk_string,
    serialize_error,
    serialize_integer,
    serialize_simple_string,
)
from store import RedisStore

sel = selectors.DefaultSelector()
store = RedisStore(max_keys=1000)

def handle_command(args: list[str]) -> bytes:
    if not args:
        return serialize_error("empty command")
    cmd = args[0].upper()
    
    if cmd == "PING":
        return serialize_simple_string("PONG")
    elif cmd == "HELLO":
        return serialize_error("unknown command 'HELLO'")
    elif cmd == "ECHO":
        return serialize_bulk_string(args[1] if len(args) > 1 else "")
    elif cmd == "SET":
        if len(args) < 3:
            return serialize_error("wrong number of arguments for 'set' command")
        key, val = args[1], args[2]
        ttl = None
        if len(args) >= 5 and args[3].upper() == "EX":
            try:
                ttl = int(args[4])
            except ValueError:
                return serialize_error("value is not an integer or out of range")
        store.set(key, val, ttl)
        return serialize_simple_string("OK")
    elif cmd == "GET":
        if len(args) != 2:
            return serialize_error("wrong number of arguments for 'get' command")
        return serialize_bulk_string(store.get(args[1]))
    elif cmd == "DEL":
        if len(args) < 2:
            return serialize_error("wrong number of arguments for 'del' command")
        return serialize_integer(sum(store.delete(k) for k in args[1:]))
    elif cmd == "EXISTS":
        if len(args) < 2:
            return serialize_error("wrong number of arguments for 'exists' command")
        return serialize_integer(sum(store.exists(k) for k in args[1:]))
    
    return serialize_error(f"unknown command '{cmd}'")

def accept_connection(server_sock):
    conn, addr = server_sock.accept()
    conn.setblocking(False)
    sel.register(conn, selectors.EVENT_READ, data=b"")

def service_connection(key, mask):
    sock = key.fileobj
    buffer = key.data

    if mask & selectors.EVENT_READ:
        try:
            recv_data = sock.recv(1024)
        except ConnectionResetError:
            recv_data = None

        if recv_data:
            buffer += recv_data
            # FIX: Loop to process all commands sent in a single burst (Pipelining)
            while True:
                args, remaining = parse_resp_array(buffer)
                if args:
                    response = handle_command(args)
                    sock.sendall(response)
                    buffer = remaining
                else:
                    break
            sel.modify(sock, selectors.EVENT_READ, data=buffer)
        else:
            sel.unregister(sock)
            sock.close()

def main(host="127.0.0.1", port=6379):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen()
    server.setblocking(False)
    sel.register(server, selectors.EVENT_READ, data=None)
    
    print(f"[*] Mini-Redis running on {host}:{port}")
    try:
        while True:
            events = sel.select(timeout=None)
            for key, mask in events:
                if key.data is None:
                    accept_connection(key.fileobj)
                else:
                    service_connection(key, mask)
    except KeyboardInterrupt:
        print("\nStopping server...")
    finally:
        sel.close()
        server.close()

if __name__ == "__main__":
    main()