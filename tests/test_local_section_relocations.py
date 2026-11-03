import struct
import tempfile
import unittest
from pathlib import Path
from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k
from tools.local_section_relocations import resolve_local_sections

ROOT = Path(__file__).resolve().parents[1]

class LocalSectionRelocationTests(unittest.TestCase):
    def test_aligned_readonly_data_and_window_limit(self):
        with tempfile.TemporaryDirectory() as tmp:
            src=Path(tmp)/'fixture.cpp';obj=Path(tmp)/'fixture.o'
            src.write_text('static const unsigned char data[8] __attribute__((aligned(8))) = {1,2,3,4,5,6,7,8}; extern "C" const unsigned char* section_fixture() { return data; }')
            result=compile_tu_armv6k(src,obj,ROOT)
            self.assertEqual(result.returncode,0,result.stderr)
            raw,relocs=extract_elf_functions_detailed(obj)['section_fixture']
            self.assertEqual(len(relocs),1)
            for base in (0x100000,0x100004):
                blob=bytearray(raw)
                handled=resolve_local_sections(obj,'section_fixture',base,blob,128)
                self.assertEqual(handled,{relocs[0].offset})
                addr=struct.unpack_from('<I',blob,relocs[0].offset)[0]
                self.assertEqual(addr%8,0)
                self.assertEqual(blob[addr-base:addr-base+8],bytes(range(1,9)))
            with self.assertRaises(ValueError):
                resolve_local_sections(obj,'section_fixture',0x100004,bytearray(raw),len(raw))

if __name__=='__main__': unittest.main()
