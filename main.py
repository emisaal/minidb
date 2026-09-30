from pathlib import Path
import struct

ENDIANNESS, SOH, VT, EOT = '<', 1, 11, 4

class Database:
    def __init__(self, db_file: str):
        """Open existing db or create new one."""

        self.db = Path(db_file)
        self.db.touch(exist_ok=True)

    def collection(self, name: str):
        """Return existing table or create new one."""

        return Collection(name=name, db=self.db)


class Collection:
    """Record structure: SOH + collection + VT + key, value_type, value + EOT."""
    def __init__(self, name: str, db: Path):
        """Open existing db table or create new one."""

        self.name = name
        self.db = db

    def put(self, key: str, value: str | int):
        """Add new key-value pair."""

        record = serialize((self.name, key, value))

        with self.db.open("a+b") as db:
            db.write(record)

    def get(self, key: str):
        # Example
        # record = b'raymond   \x32\x12\x08\x01\x08'
        # name, serialnum, school, gradelevel = unpack('<10sHHb', record)
        pass

def serialize(data: tuple) -> bytes:
    data_type = {
        int: 'h',
        str: 's'
    }
    collection, key, value = data

    collection_len = len(collection)
    collection_format = f'h{collection_len}s'
    collection = collection.encode("ascii")

    key_len = len(key)
    key_format = f'h{key_len}s'
    key = key.encode("ascii")

    value_len, value_format = 1, 'hh'
    if isinstance(value, str):
        value_len = len(value)
        value_format = f'h{value_len}s'
        value = value.encode("ascii")

    # < + SOH + collection, VT, key, VT, name (length + name) + EOT
    data_format = ENDIANNESS + 'h' + collection_format + 'h' + key_format + 'h' + value_format + 'h'
    record = struct.pack(data_format, SOH, collection_len, collection, VT, key_len, key, VT, value_len, value, EOT)

    return record

if __name__ == "__main__":
    db = Database("data.bin")
    links = db.collection("links")
    links.put("polarion", "polarion_link")
    links.put("azure", "azure_link")
    links.put("polarion", "https://polarion.gpdm.fmcglobal.net/polarion/")
    links.put("azure", "https://dev.azure.com/FreseniusMedicalCare/VSM")
    users = db.collection("users")
    users.put("alice", 31)
    users.put("bob", 27)
    # user = users.get("alice")
    # users.delete("bob")
    # result = users.query(
    #     lambda user: user["age"] > 30
    # )
