#!/usr/bin/env python3
import os
import sys
import json

sys.path.insert(0, '.')
from decrypt_getapp import load_config

os.makedirs('decrypted', exist_ok=True)

print(f"{'ID':<5} {'sn':<15} {'country':<8} {'amount':<10} {'created':<20} {'wss':<60}")
print('-' * 130)

def rank(x):
    split = x.split('.')[0]
    if split.isdigit():
        return int(split)
    return 999

for fname in sorted(os.listdir('configs'), key=rank):
    
    try:
        with open(f'configs/{fname}') as f:
            resp = json.load(f)

        if resp.get('code') != 200:
            continue

        cfg = load_config(resp['data'])

        with open(f"decrypted/{cfg['sn']}_id{cfg['id']}.json", 'w') as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)

        print(f"{cfg['id']:<5} {cfg['sn']:<15} {cfg['country']:<8} {cfg['pay_amount']:<10} {cfg['created_at']:<20} {cfg.get('wss_server','')[:60]}")
    
    except (ValueError, KeyError) as e:
        print(f"  {fname}: error - {e}")