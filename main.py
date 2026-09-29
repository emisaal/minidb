from pathlib import Path
import struct

class Database:
    def __init__(self, db_file: str):
        """Open existing db or create new one."""

        self.db = Path(db_file)
        self.db.touch(exist_ok=True)

    def collection(self, name: str):
        """Return existing table or create new one."""

        # TODO Find records for only one table in db
        return Collection(name=name, db=self.db)


class Collection:
    def __init__(self, name: str, db: Path):
        """Open existing db table or create new one."""

        self.name = name
        self.db = db

    def put(self, key: str, value: any):
        """Add new key-value pair."""

        # Example
        # record = b'raymond   \x32\x12\x08\x01\x08'
        # name, serialnum, school, gradelevel = unpack('<10sHHb', record)

        with self.db.open("a") as db:
            # TODO struct.pack
            db.write(f'{self.name}, {key}, {value}')


if __name__ == "__main__":
    db = Database("data.db")
    links = db.collection("links")
    links.put("polarion", "https://polarion.gpdm.fmcglobal.net/polarion/")
    links.put("azure", "https://dev.azure.com/FreseniusMedicalCare/VSM")
    users = db.collection("users")
    users.put("alice", {"name": "Alice", "age": 31, "country": "LT", })
    users.put("bob", {"name": "Bob", "age": 27, "country": "DE", })
    # user = users.get("alice")
    # users.delete("bob")
    # result = users.query(
    #     lambda user: user["age"] > 30
    # )
