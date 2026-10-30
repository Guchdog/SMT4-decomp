import csv
import struct
import tempfile
import unittest
from pathlib import Path

from tools.h2_mapper_production_patch import (
    OBJECTS,
    SPAN,
    audit_interior_references,
    validate_mapper_blob,
)


MAPPER_A = bytes.fromhex(
    "24209fe50010a0e10000a0e30230d0e7030051e11eff2f91010080e20b0050e3"
    "f9ffff1a0000a0e31eff2fe1eb774000"
)


class MapperProductionPatchTests(unittest.TestCase):
    def test_validates_production_literal_and_return_layout(self):
        result = validate_mapper_blob(MAPPER_A, 0x002CAB70, 0x004077EB)
        self.assertEqual(result["literal_vma"], "0x2cab9c")
        self.assertEqual(result["literal_value"], "0x4077eb")

    def test_rejects_wrong_table_literal(self):
        body = bytearray(MAPPER_A)
        struct.pack_into("<I", body, 44, 0x004077F6)
        with self.assertRaisesRegex(ValueError, "does not select"):
            validate_mapper_blob(bytes(body), 0x002CAB70, 0x004077EB)

    def test_rejects_branch_into_literal_tail(self):
        body = bytearray(MAPPER_A)
        struct.pack_into("<I", body, 36, 0xEA000000)
        with self.assertRaisesRegex(ValueError, "leaves its executable prefix"):
            validate_mapper_blob(bytes(body), 0x002CAB70, 0x004077EB)

    def test_interior_reference_scan_finds_direct_branch(self):
        image = bytearray(0x00200000)
        address = 0x00100000
        target = 0x0021F3A0
        displacement = target - address - 8
        struct.pack_into("<I", image, 0, 0xEA000000 | ((displacement >> 2) & 0xFFFFFF))
        with tempfile.TemporaryDirectory() as tmp:
            functions = Path(tmp) / "functions.csv"
            with functions.open("w", newline="", encoding="utf-8") as stream:
                writer = csv.DictWriter(stream, fieldnames=("address", "size", "name"))
                writer.writeheader()
                writer.writerow({"address": "0x00100000", "size": 4, "name": "caller"})
                for addr in OBJECTS:
                    writer.writerow({"address": hex(addr), "size": SPAN, "name": "mapper"})
            with self.assertRaisesRegex(ValueError, "external mapper interior references"):
                audit_interior_references(bytes(image), functions)


if __name__ == "__main__":
    unittest.main()
