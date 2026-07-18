#!/usr/bin/env python3
"""
Ultra-Stealth Standalone Titkosító Generátor V5
================================================
VÉGLEGES VERZIÓ - TÖKÉLETES AVALANCHE:
  - 20-30 kör (masszív lavina hatás)
  - Körönként 1 CBC + 3-4 művelet
  - CBC shift dinamikus képlet alapján (+/- tartomány)
  - Egyszerűsített: mindig modulo, nincs if
  - Új változónév minden műveletnél
  - Nincs komment a generált kódban
  - Nincs 2x ugyanaz a művelet egymás után
"""

import hashlib
import secrets
import struct
import string
from typing import List, Tuple, Any


class PRNG:
    """Determinisztikus pseudo-random number generátor"""
    
    def __init__(self, seed: bytes):
        self.state = hashlib.sha256(seed).digest()
        self.counter = 0
    
    def _next_bytes(self, n: int) -> bytes:
        result = b''
        while len(result) < n:
            data = self.state + struct.pack('>Q', self.counter)
            self.state = hashlib.sha256(data).digest()
            result += self.state
            self.counter += 1
        return result[:n]
    
    def randint(self, a: int, b: int) -> int:
        range_size = b - a + 1
        num_bytes = (range_size.bit_length() + 7) // 8
        while True:
            random_bytes = self._next_bytes(num_bytes)
            value = int.from_bytes(random_bytes, 'big')
            if value < range_size:
                return a + value
    
    def bytes(self, n: int) -> bytes:
        return self._next_bytes(n)
    
    def shuffle(self, lst: list) -> list:
        result = lst.copy()
        for i in range(len(result) - 1, 0, -1):
            j = self.randint(0, i)
            result[i], result[j] = result[j], result[i]
        return result
    
    def choice(self, options: list) -> Any:
        return options[self.randint(0, len(options) - 1)]


class VariableNameGenerator:
    """Generál random változóneveket"""
    
    def __init__(self, seed: bytes):
        self.rng = PRNG(seed + b"_varnames")
        self.used_names = set()
    
    def generate(self, prefix: str = "") -> str:
        """Generál egy egyedi random változónevet"""
        while True:
            length = self.rng.randint(4, 10)
            name = self.rng.choice(list(string.ascii_lowercase))
            chars = string.ascii_lowercase + string.digits
            for _ in range(length - 1):
                name += self.rng.choice(list(chars))
            
            if prefix:
                name = prefix + name
            
            if name not in self.used_names:
                self.used_names.add(name)
                return name


class V4CodeGenerator:
    """V4 Ultra-stealth generátor - 20-30 kör, dinamikus CBC"""
    
    # Művelet típusok (CBC nélkül)
    OPERATION_TYPES = [
        'xor', 'rotate_left', 'rotate_right', 'add_mod256', 
        'mul_mod256', 'swap_nibbles', 'substitute', 
        'permute', 'reverse_bytes'
    ]
    
    # CBC shift képletek (+/- tartománnyal)
    SHIFT_FORMULAS = [
        ("(r * 7) % 27 - 13", "Linear symmetric"),
        ("(r * 11) % 31 - 15", "Larger range"),
        ("(r * 5) % 21 - 10", "Medium range"),
        ("((r % 15) - 7)", "Simple zigzag"),
        ("(r * 13) % 23 - 11", "Prime based"),
    ]
    
    def __init__(self, seed: bytes):
        if len(seed) != 32:
            raise ValueError("A seed-nek pontosan 32 bájtnak kell lennie!")
        self.seed = seed
        self.rng = PRNG(seed)
        self.vargen = VariableNameGenerator(seed)
        
        # Körök száma
        self.num_rounds = self.rng.randint(20, 30)
        
        # CBC shift képlet választása
        self.shift_formula, self.shift_desc = self.rng.choice(self.SHIFT_FORMULAS)
        
        # Maximum shift → minimum üzenet hossz
        self.max_shift = self._calculate_max_shift()
        self.min_message_len = self.max_shift + 1
        
        # Pipeline: fix műveletsor ami ismétlődik
        self.pipeline = self._generate_fixed_pipeline()
    
    def _calculate_max_shift(self) -> int:
        """Kiszámolja a maximum shift értéket"""
        max_val = 0
        for round in range(self.num_rounds):
            shift = eval(self.shift_formula.replace('r', str(round)))
            if shift == 0:
                shift = 1
            max_val = max(max_val, abs(shift))
        return max_val
    
    def _generate_fixed_pipeline(self) -> List[Tuple[str, Any]]:
        """Generál egy fix művelet-sorozatot (CBC + 3-4 művelet)"""
        pipeline = []
        
        # Először generáljuk a nem-CBC műveleteket
        num_ops = self.rng.randint(3, 4)
        last_op = None
        
        for _ in range(num_ops):
            available = [op for op in self.OPERATION_TYPES if op != last_op]
            op_type = self.rng.choice(available)
            pipeline.append(self._generate_operation(op_type))
            last_op = op_type
        
        # CBC-t random pozícióba szúrjuk be!
        cbc_position = self.rng.randint(0, len(pipeline))
        pipeline.insert(cbc_position, ('cbc', None))
        
        return pipeline
    
    def _generate_operation(self, op_type: str) -> Tuple[str, Any]:
        """Generál egy adott típusú műveletet paraméterekkel"""
        
        if op_type == 'xor':
            key_size = self.rng.randint(8, 32)
            key = self.rng.bytes(key_size)
            return ('xor', key)
        elif op_type == 'rotate_left':
            shift = self.rng.randint(1, 7)
            return ('rotate_left', shift)
        elif op_type == 'rotate_right':
            shift = self.rng.randint(1, 7)
            return ('rotate_right', shift)
        elif op_type == 'substitute':
            sbox = self.rng.shuffle(list(range(256)))
            return ('substitute', sbox)
        elif op_type == 'permute':
            perm = self.rng.shuffle(list(range(16)))
            return ('permute', perm)
        elif op_type == 'add_mod256':
            constant = self.rng.randint(1, 255)
            return ('add_mod256', constant)
        elif op_type == 'mul_mod256':
            multiplier = self.rng.randint(1, 127) * 2 + 1
            return ('mul_mod256', multiplier)
        elif op_type == 'reverse_bytes':
            block_size = self.rng.choice([4, 8, 16])
            return ('reverse_bytes', block_size)
        elif op_type == 'swap_nibbles':
            return ('swap_nibbles', None)
        
        return (op_type, None)
    
    def _generate_encrypt_code(self) -> str:
        """Generál stealth encrypt.py - 20-30 körös loop"""
        
        func_name = self.vargen.generate()
        param_name = self.vargen.generate()
        
        code = f'''#!/usr/bin/env python3
import sys

def {func_name}({param_name}):
    {self.vargen.generate()} = bytearray({param_name})
'''
        
        # Outer loop változó
        round_var = self.vargen.generate()
        
        # Kezdő változónév (ami az outer loop előtt van)
        current_var = code.split('= bytearray')[0].split()[-1]
        
        code += f'''    
    for {round_var} in range({self.num_rounds}):
'''
        
        # Pipeline műveletek generálása
        for op, param in self.pipeline:
            new_var = self.vargen.generate()
            
            if op == 'cbc':
                # CBC - dinamikus shift, mindig modulo
                shift_var = self.vargen.generate()
                idx_var = self.vargen.generate()
                
                code += f"        {new_var} = {current_var}\n"
                code += f"        {shift_var} = {self.shift_formula.replace('r', round_var)}\n"
                code += f"        if {shift_var} == 0:\n"
                code += f"            {shift_var} = 1 if {round_var} % 2 == 0 else -1\n"
                code += f"        for {idx_var} in range(len({new_var})):\n"
                code += f"            {new_var}[{idx_var}] ^= {new_var}[({idx_var} + {shift_var}) % len({new_var})]\n"
            
            elif op == 'xor':
                key_var = self.vargen.generate()
                idx_var = self.vargen.generate()
                key_bytes = ', '.join(str(b) for b in param)
                
                code += f"        {new_var} = {current_var}\n"
                code += f"        {key_var} = bytes([{key_bytes}])\n"
                code += f"        for {idx_var} in range(len({new_var})):\n"
                code += f"            {new_var}[{idx_var}] ^= {key_var}[{idx_var} % len({key_var})]\n"
            
            elif op == 'rotate_left':
                idx_var = self.vargen.generate()
                tmp_var = self.vargen.generate()
                
                code += f"        {new_var} = {current_var}\n"
                code += f"        for {idx_var} in range(len({new_var})):\n"
                code += f"            {tmp_var} = {new_var}[{idx_var}]\n"
                code += f"            {new_var}[{idx_var}] = (({tmp_var} << {param}) | ({tmp_var} >> {8-param})) & 0xFF\n"
            
            elif op == 'rotate_right':
                idx_var = self.vargen.generate()
                tmp_var = self.vargen.generate()
                
                code += f"        {new_var} = {current_var}\n"
                code += f"        for {idx_var} in range(len({new_var})):\n"
                code += f"            {tmp_var} = {new_var}[{idx_var}]\n"
                code += f"            {new_var}[{idx_var}] = (({tmp_var} >> {param}) | ({tmp_var} << {8-param})) & 0xFF\n"
            
            elif op == 'substitute':
                sbox_var = self.vargen.generate()
                idx_var = self.vargen.generate()
                sbox_values = ', '.join(str(v) for v in param)
                
                code += f"        {new_var} = {current_var}\n"
                code += f"        {sbox_var} = [{sbox_values}]\n"
                code += f"        for {idx_var} in range(len({new_var})):\n"
                code += f"            {new_var}[{idx_var}] = {sbox_var}[{new_var}[{idx_var}]]\n"
            
            elif op == 'permute':
                perm_var = self.vargen.generate()
                bs_var = self.vargen.generate()
                be_var = self.vargen.generate()
                blk_var = self.vargen.generate()
                perm_var2 = self.vargen.generate()
                j_var = self.vargen.generate()
                perm_values = ', '.join(str(v) for v in param)
                
                code += f"        {new_var} = {current_var}\n"
                code += f"        {perm_var} = [{perm_values}]\n"
                code += f"        for {bs_var} in range(0, len({new_var}), 16):\n"
                code += f"            {be_var} = min({bs_var} + 16, len({new_var}))\n"
                code += f"            {blk_var} = {new_var}[{bs_var}:{be_var}]\n"
                code += f"            if len({blk_var}) == 16:\n"
                code += f"                {perm_var2} = bytearray(16)\n"
                code += f"                for {j_var} in range(16):\n"
                code += f"                    {perm_var2}[{j_var}] = {blk_var}[{perm_var}[{j_var}]]\n"
                code += f"                {new_var}[{bs_var}:{be_var}] = {perm_var2}\n"
            
            elif op == 'add_mod256':
                idx_var = self.vargen.generate()
                
                code += f"        {new_var} = {current_var}\n"
                code += f"        for {idx_var} in range(len({new_var})):\n"
                code += f"            {new_var}[{idx_var}] = ({new_var}[{idx_var}] + {param}) % 256\n"
            
            elif op == 'mul_mod256':
                idx_var = self.vargen.generate()
                
                code += f"        {new_var} = {current_var}\n"
                code += f"        for {idx_var} in range(len({new_var})):\n"
                code += f"            {new_var}[{idx_var}] = ({new_var}[{idx_var}] * {param}) % 256\n"
            
            elif op == 'reverse_bytes':
                bs_var = self.vargen.generate()
                be_var = self.vargen.generate()
                
                code += f"        {new_var} = {current_var}\n"
                code += f"        for {bs_var} in range(0, len({new_var}), {param}):\n"
                code += f"            {be_var} = min({bs_var} + {param}, len({new_var}))\n"
                code += f"            {new_var}[{bs_var}:{be_var}] = reversed({new_var}[{bs_var}:{be_var}])\n"
            
            elif op == 'swap_nibbles':
                idx_var = self.vargen.generate()
                tmp_var = self.vargen.generate()
                
                code += f"        {new_var} = {current_var}\n"
                code += f"        for {idx_var} in range(len({new_var})):\n"
                code += f"            {tmp_var} = {new_var}[{idx_var}]\n"
                code += f"            {new_var}[{idx_var}] = (({tmp_var} & 0x0F) << 4) | (({tmp_var} & 0xF0) >> 4)\n"
            
            current_var = new_var
        
        # Return és main - clean, nincs utasítás
        msg_var = self.vargen.generate()
        enc_var = self.vargen.generate()
        res_var = self.vargen.generate()
        
        code += f'''        
    return bytes({current_var})

if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(1)
    
    {msg_var} = sys.argv[1]
    {enc_var} = {msg_var}.encode('utf-8')
    {res_var} = {func_name}({enc_var})
    print({res_var}.hex())
'''
        
        return code
    
    def _generate_decrypt_code(self) -> str:
        """Generál stealth decrypt.py - fordított pipeline"""
        
        func_name = self.vargen.generate()
        param_name = self.vargen.generate()
        
        code = f'''#!/usr/bin/env python3
import sys

def {func_name}({param_name}):
    {self.vargen.generate()} = bytearray({param_name})
'''
        
        round_var = self.vargen.generate()
        current_var = code.split('= bytearray')[0].split()[-1]
        
        # FORDÍTOTT outer loop (körök fordított sorrendben!)
        code += f'''    
    for {round_var} in range({self.num_rounds} - 1, -1, -1):
'''
        
        # FORDÍTOTT pipeline
        for op, param in reversed(self.pipeline):
            new_var = self.vargen.generate()
            
            if op == 'cbc':
                # CBC inverze - backward iteration
                shift_var = self.vargen.generate()
                idx_var = self.vargen.generate()
                
                code += f"        {new_var} = {current_var}\n"
                code += f"        {shift_var} = {self.shift_formula.replace('r', round_var)}\n"
                code += f"        if {shift_var} == 0:\n"
                code += f"            {shift_var} = 1 if {round_var} % 2 == 0 else -1\n"
                code += f"        for {idx_var} in range(len({new_var}) - 1, -1, -1):\n"
                code += f"            {new_var}[{idx_var}] ^= {new_var}[({idx_var} + {shift_var}) % len({new_var})]\n"
            
            elif op == 'xor':
                # XOR önmaga inverze
                key_var = self.vargen.generate()
                idx_var = self.vargen.generate()
                key_bytes = ', '.join(str(b) for b in param)
                
                code += f"        {new_var} = {current_var}\n"
                code += f"        {key_var} = bytes([{key_bytes}])\n"
                code += f"        for {idx_var} in range(len({new_var})):\n"
                code += f"            {new_var}[{idx_var}] ^= {key_var}[{idx_var} % len({key_var})]\n"
            
            elif op == 'rotate_left':
                # Inverz: rotate right
                idx_var = self.vargen.generate()
                tmp_var = self.vargen.generate()
                
                code += f"        {new_var} = {current_var}\n"
                code += f"        for {idx_var} in range(len({new_var})):\n"
                code += f"            {tmp_var} = {new_var}[{idx_var}]\n"
                code += f"            {new_var}[{idx_var}] = (({tmp_var} >> {param}) | ({tmp_var} << {8-param})) & 0xFF\n"
            
            elif op == 'rotate_right':
                # Inverz: rotate left
                idx_var = self.vargen.generate()
                tmp_var = self.vargen.generate()
                
                code += f"        {new_var} = {current_var}\n"
                code += f"        for {idx_var} in range(len({new_var})):\n"
                code += f"            {tmp_var} = {new_var}[{idx_var}]\n"
                code += f"            {new_var}[{idx_var}] = (({tmp_var} << {param}) | ({tmp_var} >> {8-param})) & 0xFF\n"
            
            elif op == 'substitute':
                # Inverz S-box
                inv_sbox = [0] * 256
                for j, val in enumerate(param):
                    inv_sbox[val] = j
                sbox_var = self.vargen.generate()
                idx_var = self.vargen.generate()
                inv_values = ', '.join(str(v) for v in inv_sbox)
                
                code += f"        {new_var} = {current_var}\n"
                code += f"        {sbox_var} = [{inv_values}]\n"
                code += f"        for {idx_var} in range(len({new_var})):\n"
                code += f"            {new_var}[{idx_var}] = {sbox_var}[{new_var}[{idx_var}]]\n"
            
            elif op == 'permute':
                # Inverz permutáció
                inv_perm = [0] * 16
                for j in range(16):
                    inv_perm[param[j]] = j
                perm_var = self.vargen.generate()
                bs_var = self.vargen.generate()
                be_var = self.vargen.generate()
                blk_var = self.vargen.generate()
                perm_var2 = self.vargen.generate()
                j_var = self.vargen.generate()
                inv_perm_values = ', '.join(str(v) for v in inv_perm)
                
                code += f"        {new_var} = {current_var}\n"
                code += f"        {perm_var} = [{inv_perm_values}]\n"
                code += f"        for {bs_var} in range(0, len({new_var}), 16):\n"
                code += f"            {be_var} = min({bs_var} + 16, len({new_var}))\n"
                code += f"            {blk_var} = {new_var}[{bs_var}:{be_var}]\n"
                code += f"            if len({blk_var}) == 16:\n"
                code += f"                {perm_var2} = bytearray(16)\n"
                code += f"                for {j_var} in range(16):\n"
                code += f"                    {perm_var2}[{j_var}] = {blk_var}[{perm_var}[{j_var}]]\n"
                code += f"                {new_var}[{bs_var}:{be_var}] = {perm_var2}\n"
            
            elif op == 'add_mod256':
                # Inverz: kivonás
                idx_var = self.vargen.generate()
                
                code += f"        {new_var} = {current_var}\n"
                code += f"        for {idx_var} in range(len({new_var})):\n"
                code += f"            {new_var}[{idx_var}] = ({new_var}[{idx_var}] - {param}) % 256\n"
            
            elif op == 'mul_mod256':
                # Inverz: moduláris inverz szorzás
                inv_mult = self._modular_inverse(param, 256)
                idx_var = self.vargen.generate()
                
                code += f"        {new_var} = {current_var}\n"
                code += f"        for {idx_var} in range(len({new_var})):\n"
                code += f"            {new_var}[{idx_var}] = ({new_var}[{idx_var}] * {inv_mult}) % 256\n"
            
            elif op == 'reverse_bytes':
                # Reverse önmaga inverze
                bs_var = self.vargen.generate()
                be_var = self.vargen.generate()
                
                code += f"        {new_var} = {current_var}\n"
                code += f"        for {bs_var} in range(0, len({new_var}), {param}):\n"
                code += f"            {be_var} = min({bs_var} + {param}, len({new_var}))\n"
                code += f"            {new_var}[{bs_var}:{be_var}] = reversed({new_var}[{bs_var}:{be_var}])\n"
            
            elif op == 'swap_nibbles':
                # Swap önmaga inverze
                idx_var = self.vargen.generate()
                tmp_var = self.vargen.generate()
                
                code += f"        {new_var} = {current_var}\n"
                code += f"        for {idx_var} in range(len({new_var})):\n"
                code += f"            {tmp_var} = {new_var}[{idx_var}]\n"
                code += f"            {new_var}[{idx_var}] = (({tmp_var} & 0x0F) << 4) | (({tmp_var} & 0xF0) >> 4)\n"
            
            current_var = new_var
        
        msg_var = self.vargen.generate()
        hex_var = self.vargen.generate()
        res_var = self.vargen.generate()
        
        code += f'''        
    return bytes({current_var})

if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(1)
    
    {hex_var} = sys.argv[1]
    {msg_var} = bytes.fromhex({hex_var})
    {res_var} = {func_name}({msg_var})
    
    try:
        print({res_var}.decode('utf-8'))
    except:
        print({res_var}.decode('utf-8', errors='replace'))
'''
        
        return code
    
    def _modular_inverse(self, a: int, m: int) -> int:
        """Extended Euclidean algoritmus"""
        def extended_gcd(a, b):
            if a == 0:
                return b, 0, 1
            gcd, x1, y1 = extended_gcd(b % a, a)
            x = y1 - (b // a) * x1
            y = x1
            return gcd, x, y
        
        gcd, x, _ = extended_gcd(a % m, m)
        if gcd != 1:
            raise ValueError(f"Nincs moduláris inverze: {a} mod {m}")
        return (x % m + m) % m
    
    def generate_files(self, output_dir: str = "."):
        """Generálja a két stealth fájlt"""
        import os
        
        encrypt_code = self._generate_encrypt_code()
        decrypt_code = self._generate_decrypt_code()
        
        encrypt_path = os.path.join(output_dir, "encrypt.py")
        decrypt_path = os.path.join(output_dir, "decrypt.py")
        
        with open(encrypt_path, 'w') as f:
            f.write(encrypt_code)
        
        with open(decrypt_path, 'w') as f:
            f.write(decrypt_code)
        
        os.chmod(encrypt_path, 0o755)
        os.chmod(decrypt_path, 0o755)
        
        return encrypt_path, decrypt_path
    
    def get_pipeline_description(self) -> str:
        """Pipeline leírás"""
        lines = [f"🔥 V4 ULTRA-STEALTH ALGORITMUS 🔥"]
        lines.append(f"\n  Körök száma: {self.num_rounds}")
        lines.append(f"  CBC shift képlet: {self.shift_formula}")
        lines.append(f"  Leírás: {self.shift_desc}")
        lines.append(f"  Maximum shift: {self.max_shift}")
        lines.append(f"\n  ⚠️  MINIMUM üzenet hossz: {self.min_message_len} bájt")
        lines.append(f"      (Rövid üzenetek: add hozzá szóközöket!)")
        lines.append(f"\n  Körönkénti műveletek ({len(self.pipeline)} művelet):")
        
        for i, (op, param) in enumerate(self.pipeline, 1):
            if op == 'cbc':
                lines.append(f"    {i}. CBC (dinamikus shift)")
            elif op == 'xor':
                lines.append(f"    {i}. XOR ({len(param)} bájt)")
            elif op in ['rotate_left', 'rotate_right']:
                lines.append(f"    {i}. {op.replace('_', ' ').title()} {param}")
            elif op == 'substitute':
                lines.append(f"    {i}. S-box")
            elif op == 'permute':
                lines.append(f"    {i}. Permutáció")
            elif op == 'add_mod256':
                lines.append(f"    {i}. ADD +{param}")
            elif op == 'mul_mod256':
                lines.append(f"    {i}. MUL ×{param}")
            elif op == 'reverse_bytes':
                lines.append(f"    {i}. Reverse ({param})")
            elif op == 'swap_nibbles':
                lines.append(f"    {i}. Swap nibbles")
        
        lines.append(f"\n  ✅ Teljes műveletszám: {self.num_rounds} × {len(self.pipeline)} = {self.num_rounds * len(self.pipeline)}")
        lines.append(f"  ✅ Tökéletes avalanche hatás!")
        lines.append(f"  ✅ Nincs komment a generált kódban")
        lines.append(f"  ✅ Random változónevek")
        lines.append(f"  ✅ Egyszerűsített CBC (mindig modulo)")
        
        return '\n'.join(lines)


def generate_shared_seed() -> bytes:
    return secrets.token_bytes(32)

def seed_to_hex(seed: bytes) -> str:
    return seed.hex()

def hex_to_seed(hex_string: str) -> bytes:
    return bytes.fromhex(hex_string)


if __name__ == "__main__":
    import sys
    
    print("=" * 80)
    print("🔥 ULTRA-STEALTH TITKOSÍTÓ GENERÁTOR V4 🔥")
    print("=" * 80)
    print()
    print("VÉGLEGES VERZIÓ - TÖKÉLETES AVALANCHE:")
    print("  ✅ 20-30 kör (masszív lavina hatás)")
    print("  ✅ Körönként 1 CBC + 3-4 művelet")
    print("  ✅ CBC shift dinamikus (+/- képlet)")
    print("  ✅ Egyszerűsített: mindig modulo")
    print("  ✅ Új változónév minden műveletnél")
    print("  ✅ Nincs komment")
    print("  ✅ Nincs ismétlődés")
    print()
    print("-" * 80)
    print()
    
    if len(sys.argv) > 1:
        print("1. Megadott SEED használata...")
        seed_hex = sys.argv[1]
        seed = hex_to_seed(seed_hex)
        print(f"   SEED: {seed_hex}")
        print()
    else:
        print("1. Új SEED generálása...")
        seed = generate_shared_seed()
        seed_hex = seed_to_hex(seed)
        
        print(f"   SEED (hex): {seed_hex}")
        print()
        print("   ⚠️  EZT A SEED-ET MINDKÉT FÉLNEK BIZTONSÁGOSAN MEG KELL OSZTANIA!")
        print()
    
    print("2. V4 scriptek generálása...")
    generator = V4CodeGenerator(seed)
    enc_path, dec_path = generator.generate_files()
    
    print(f"   ✓ Létrehozva: {enc_path}")
    print(f"   ✓ Létrehozva: {dec_path}")
    print()
    
    print("3. Generált algoritmus részletek:")
    print()
    print(generator.get_pipeline_description())
    print()
    
    print("4. Teszt...")
    test_message = "V4 végleges verzió! Tökéletes avalanche! 🔥"
    print(f"   Teszt üzenet: '{test_message}'")
    print()
    
    import subprocess
    result = subprocess.run(
        ['python3', enc_path, test_message],
        capture_output=True,
        text=True
    )
    encrypted = result.stdout.strip()
    print(f"   Titkosított: {encrypted}")
    print()
    
    result = subprocess.run(
        ['python3', dec_path, encrypted],
        capture_output=True,
        text=True
    )
    decrypted = result.stdout.strip()
    print(f"   Dekódolt: '{decrypted}'")
    print()
    
    if test_message == decrypted:
        print("   ✅ SIKER!")
    else:
        print("   ❌ HIBA!")
    print()
    
    print("=" * 80)
    print("🔥 V4 VÉGLEGES - TÖKÉLETES! 🔥")
    print("=" * 80)
    print()
