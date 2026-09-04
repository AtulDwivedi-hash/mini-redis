def serialize_simple_string(text: str) -> bytes:
    return f"+{text}\r\n".encode()

def serialize_error(message: str) -> bytes:
    return f"-ERR {message}\r\n".encode()

def serialize_bulk_string(text: str | None) -> bytes:
    if text is None:
        return b"$-1\r\n"
    data = text.encode()
    return f"${len(data)}\r\n".encode() + data + b"\r\n"

def serialize_integer(num: int) -> bytes:
    return f":{num}\r\n".encode()

def parse_resp_array(buffer: bytes):
    if not buffer.startswith(b"*"):
        return None, buffer

    lines = buffer.split(b"\r\n")
    try:
        count = int(lines[0][1:])
    except ValueError:
        return None, buffer

    expected_lines = 1 + (count * 2)
    if len(lines) < expected_lines:
        return None, buffer

    args = []
    idx = 1
    for _ in range(count):
        val = lines[idx + 1].decode("utf-8", errors="replace")
        args.append(val)
        idx += 2

    # FIX: Correctly calculates consumed bytes to cleanly slice the buffer
    consumed_bytes = sum(len(line) + 2 for line in lines[:expected_lines])
    remaining = buffer[consumed_bytes:]
    return args, remaining