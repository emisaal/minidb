import time
from dataclasses import dataclass
from pathlib import Path
import struct
from typing import Self

ENDIAN = '>'
STX = struct.pack('B', 2)
ETX = struct.pack('B', 3)
RECORD_SEPARATOR = struct.pack('B', 30)
DATA_SEPARATOR = struct.pack('B', 11)
INT, STR = 20, 21


@dataclass
class Record:
    collection: str = None
    key: str = None
    value: str | int = None
    active: int = 1

    @classmethod
    def from_bytes(cls, data: bytes) -> Self:
        """Convert data and return class instance."""

        _, collection, key, value, active, _ = data.split(DATA_SEPARATOR)

        return cls(
            collection=cls.decode_value(collection),
            key=cls.decode_value(key),
            value=cls.decode_value(value),
            active=cls.decode_value(active)
        )

    def encode_record(self) -> bytes:
        """Encode string/int into a data pack containing: {delimiter, type, length, value, active}."""

        data = b''
        for val in self.collection, self.key, self.value, self.active:
            data += DATA_SEPARATOR
            data += self.encode_value(val)

        return RECORD_SEPARATOR + STX + data + DATA_SEPARATOR + ETX

    def encode_value(self, value: str | int) -> bytes:
        """Encode provided value into bytes."""

        if isinstance(value, int):
            return struct.pack(f'{ENDIAN}BHHB', INT, 1, value, self.active)
        return struct.pack(f'{ENDIAN}BH{len(value)}sB', STR, len(value), value.encode("ascii"), self.active)

    @staticmethod
    def decode_value(data: bytes) -> str | int:
        """Unpack data into string/int."""

        string_value = data [0] == STR
        length = data[2] + (data[1] << 8)
        type_ = f'{length}s' if string_value else 'H'
        _, _, value, _ = struct.unpack(f'{ENDIAN}BH{type_}B', data)

        value = value.decode("ascii") if string_value else value
        # print(f'unpack_value: {data} -> {value}')
        return value


class Database:
    def __init__(self, db_file: str):
        """Open existing db or create new one."""

        self.db = Path(db_file)
        self.db.touch(exist_ok=True)
        self.data_dict = {}
        self.prepare_active_data()

    def collection(self, name: str):
        """Return existing table or create new one."""

        return Collection(name=name, database=self)

    def prepare_active_data(self):
        """Get active data."""

        data = self.db.read_bytes()
        if len(data) == 0:
            return

        data_dict = {}
        records = data.split(RECORD_SEPARATOR)

        for record in records:
            if record == b'':
                continue

            curr_record = Record.from_bytes(record)

            if curr_record.collection not in data_dict:
                data_dict[curr_record.collection] = {}

            if curr_record.active:
                data_dict[curr_record.collection][curr_record.key] = curr_record.value
            else:
                data_dict[curr_record.collection].pop(curr_record.key, None)

        self.data_dict = data_dict

    def add_new_record(self, record: Record):
        """Add new record to the database."""

        with self.db.open("a+b") as db:
            db.write(record.encode_record())

        if record.active:
            self.data_dict[record.collection][record.key] = record.value
            return

        self.data_dict[record.collection].pop(record.key, None)


class Collection:
    def __init__(self, name: str, database: Database):
        """Open existing db table or create new one."""

        self.name = name
        self.database = database
        if name not in self.database.data_dict:
            self.database.data_dict[name] = {}

    def put(self, key: str, value: str | int, active: int = 1):
        """Add new key-value pair."""

        print(f'{"Put" if active else "Delete"} {key}: {value}')
        record = Record(self.name, key, value, active)
        self.database.add_new_record(record)

    def get(self, key: str) -> str | int:
        """Get value for provided key."""

        if self.name in self.database.data_dict and self.contains(key):
            print(f'Get {key}: {self.database.data_dict[self.name][key]}')
            return self.database.data_dict[self.name][key]

    def delete(self, key: str):
        """Delete key record from db."""

        active = 0
        value = self.database.data_dict[self.name][key]
        self.put(key, value, active)

    def contains(self, key: str) -> bool:
        """Check if key is present in db."""

        return key in self.database.data_dict[self.name]


if __name__ == "__main__":
    start_time = time.time()

    db = Database("data.db")
    links = db.collection("links")
    links.put("polarion", "https://polarion.gpdm.fmcglobal.net/polarion/")
    links.get("polarion")
    links.put("azure", "https://dev.azure.com/FreseniusMedicalCare/VSM")
    links.get("azure")
    links.put("polarion", "new_link")
    links.delete("azure")
    links.get("azure")
    links.get("polarion")

    users = db.collection("users")
    users.put("alice", 31)
    users.put("bob", 27)
    user = users.get("alice")
    print(users.contains("alice"))
    users.get("bob")
    users.delete("bob")
    print(users.contains("bob"))

    end_time = time.time()
    print(f'Time taken: {round(end_time - start_time, 2)} s')
    # result = users.query(
    #     lambda user: user["age"] > 30
    # )

# from pathlib import Path
# import struct
# my_db = Path("data.bin")
# my_bytes = my_db.read_bytes()
