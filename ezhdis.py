#!/usr/bin/env python3

# Disassembler for NXP's secret "EZH" microprocessor (aka IOH Arch. B, aka SmartDMA)
# Copyright (c) 2023 Aedan Cullen <aedan@aedancullen.com>
# SPDX-License-Identifier: GPL-3.0-or-later

import sys
import ezh_isa

LOAD_ADDR = 0x00100000
print("Assuming load address", "0x%08X" % LOAD_ADDR)
print(len(ezh_isa.INST), "known instruction mnemonics")

def dis_word(fh, x, addr):
    sel_mnemonic = None
    sel_fields = None
    for (mnemonic, codemask, code, fields) in ezh_isa.INST:
        if (x ^ code) & codemask == 0:
            if sel_mnemonic != None:
                print("prev sel_mnemonic:\t\t", sel_mnemonic)
                print("new sel_mnemonic:\t\t", mnemonic)
                print("Duplicate mnemonic match; exiting")
                sys.exit(1)
            sel_mnemonic = mnemonic
            sel_fields = fields
    width = 0
    if sel_mnemonic == None:
        fh.write("E_NOP")
        width += len("E_NOP")
        fh.write(" " * (40 - width) + "// " + "Unknown instruction" + "\n")
        print("Unknown instruction", "0x%08X" % x, "at address", "0x%08X" % addr)
    else:
        fh.write(sel_mnemonic)
        width += len(sel_mnemonic)
        if sel_fields != []:
            fh.write("(")
            width += 1
            i = 0
            for field_decoder in sel_fields:
                if i != 0:
                    fh.write(", ")
                    width += 2
                decoded_str = str(field_decoder(x))
                fh.write(decoded_str)
                width += len(decoded_str)
                i += 1
            fh.write(")")
            width += 1
        fh.write(" " * (40 - width) + "// " + "0x%08X" % addr + "\n")

base_file = sys.argv[-1]
base_file = base_file if not base_file.endswith(".bin") else base_file.split(".")[0]
bin_file = base_file + ".bin"

if sys.argv[1] == "-p":
    with open(base_file, "r") as fh:
        res = fh.read()
    res = res.replace("{", "[")
    res = res.replace("}", "]")
    res = res.replace("U", "")
    res = eval(res)
    bin_file = base_file + ".bin"
    with open(bin_file, "wb") as fh:
        for byte in res:
            fh.write(byte.to_bytes())
    print("Wrote binary", bin_file)

disas_file = base_file + ".h"

with open(bin_file, "rb") as fh:
    with open(disas_file, "w") as dis_out:
        dis_out.write("// Generated by ezhdis.py from ")
        dis_out.write(bin_file)
        dis_out.write("\n\n")
        dis_out.write('#include "fsl_smartdma_prv.h"\n\n')
        word = fh.read(4)
        addr = LOAD_ADDR
        while word:
            x = int.from_bytes(word, "little")
            dis_word(dis_out, x, addr)
            word = fh.read(4)
            addr += 4

print("Wrote disassembly", disas_file)
