from dataclasses import dataclass
from pathlib import Path
import struct

STX = struct.pack('h', 2)
ETX = struct.pack('h', 3)
RECORD_SEPARATOR = struct.pack('h', 30)
DATA_SEPARATOR = struct.pack('h', 11)
INT, STR = 20, 21

@dataclass
class Record:
    collection: str = None
    key: str = None
    value: str | int = None


class Database:
    def __init__(self, db_file: str):
        """Open existing db or create new one."""

        self.db = Path(db_file)
        self.db.touch(exist_ok=True)

    def collection(self, name: str):
        """Return existing table or create new one."""

        return Collection(name=name, db=self.db)


class Collection:
    """Record structure: STX + collection + VT + key, value_type, value + ETX."""

    def __init__(self, name: str, db: Path):
        """Open existing db table or create new one."""

        self.name = name
        self.db = db

    def put(self, key: str, value: str | int):
        """Add new key-value pair."""

        record = self.encode_record(key, value)
        if record in self.db.read_bytes():
            print('Skip putting record')
            return

        with self.db.open("a+b") as db:
            db.write(record)

    def get(self, key: str):
        """Get value for provided key."""

        data = self.db.read_bytes()
        records = data.split(RECORD_SEPARATOR)

        for record in records:
            if self.encode_value(self.name) in record:
                if self.encode_value(key) in record:
                    value = self.decode_record(record).value
                    print(value)
                    return value

    def delete(self, key: str):
        """Delete key record from db."""

        data = self.db.read_bytes()
        records = data.split(RECORD_SEPARATOR)
        delete_record = None

        for record in records:
            if self.encode_value(self.name) in record:
                if self.encode_value(key) in record:
                    print(self.encode_value(key))
                    delete_record = RECORD_SEPARATOR + record
                    break

        print(data)
        if delete_record is None:
            return

        data.replace(delete_record, b'')
        print(delete_record)
        print(data)
        self.db.write_bytes(data)
        print(self.db.read_bytes())

    def encode_value(self, value: str | int) -> bytes:
        """Encode provided value into bytes."""

        if isinstance(value, int):
            return struct.pack(f'hhh', INT, 1, value)
        return struct.pack(f'hh{len(value)}s', STR, len(value), value.encode("ascii"))

    def encode_record(self, key: str, value: str | int) -> bytes:
        """Encode string/int into a data pack containing: {delimiter, type, length, value}."""

        data = b''
        for val in self.name, key, value:
            data += DATA_SEPARATOR
            data += self.encode_value(val)

        return RECORD_SEPARATOR + STX + data + DATA_SEPARATOR + ETX

    def decode_record(self, record: bytes) -> Record:
        """Decode record data stored as:
        'STX, VT, collection, VT, key, VT, name + ETX'.
        """

        # b'\x02\x00\x0b\x00\x15\x00\x05\x00users\x0b\x00\x15\x00\x05\x00alice\x0b\x00\x14\x00\x01\x00\x1f\x00\x0b\x00\x03\x00'
        # STX: \x02\x00, ETX: \x03\x00, VT: \x0b\x00
        print(record)
        _, collection, key, value, _ = record.split(DATA_SEPARATOR)  # first and last values are STX and ETX

        record = Record()
        record.collection = self.unpack_value(collection)
        record.key = self.unpack_value(key)
        record.value = self.unpack_value(value)
        return record

    def unpack_value(self, data: bytes) -> str | int:
        """Unpack data into string/int. b'\x15\x00\x05\x00links' -> 'links'"""

        string_value = data [0] == STR
        type_ = f'{data[2]}s' if string_value else 'h'
        _, _, value = struct.unpack(f'hh{type_}', data)

        value = value.decode("ascii") if string_value else value
        print(f'unpack_value: {data} -> {value}')
        return value


if __name__ == "__main__":
    db = Database("data.bin")
    links = db.collection("links")
    links.put("polarion", "https://polarion.gpdm.fmcglobal.net/polarion/")
    links.put("azure", "https://dev.azure.com/FreseniusMedicalCare/VSM")
    links.get("polarion")

    users = db.collection("users")
    users.put("alice", 31)
    users.put("bob", 27)
    user = users.get("alice")
    users.delete("bob")
    # result = users.query(
    #     lambda user: user["age"] > 30
    # )

# from pathlib import Path
# import struct
# my_db = Path("data.bin")
# my_bytes = my_db.read_bytes()
