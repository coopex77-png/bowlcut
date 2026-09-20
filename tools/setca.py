#!/usr/bin/env python3
"""Point the site at a new mint. Usage: tools/setca.py <MINT> [buy_url]
Checks DexScreener. pump.fun tokens: records the bonding-curve account (DexScreener's pair address, or the PDA derived
here if it isn't indexed yet) so the site reads price straight from the chain. Otherwise, if the token isn't indexed,
finds its Raydium LaunchLab pool on-chain (via the mint's first transaction), verifies the layout and reads the quote mint.
Writes mint/pool/quote/curve into config.js."""
import json, re, struct, sys, base64, time, urllib.request

RPCS = ['https://api.mainnet-beta.solana.com', 'https://solana-rpc.publicnode.com']
LAUNCHLAB = 'LanMV9sAd7wArD4vJFi2qDdfnVhFxYSUg6eADduJ3uj'
PUMP = '6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P'
B58 = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'

def get(url):
    return json.load(urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'bowlcut/1.0'}), timeout=15))
def rpc(method, params):
    body = json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params}).encode()
    for attempt in range(4):                                   # public RPCs rate-limit bursts: back off and try the next one
        for url in RPCS:
            try:
                req = urllib.request.Request(url, data=body, headers={'content-type': 'application/json', 'User-Agent': 'Mozilla/5.0'})
                r = json.load(urllib.request.urlopen(req, timeout=20))
                if 'result' in r: return r['result']
                err = r.get('error')
            except Exception as e: err = e
        time.sleep(1.5 * (attempt + 1))
    raise SystemExit(f'rpc {method} failed: {err}')
def b58(b):
    n = int.from_bytes(b, 'big'); s = ''
    while n: n, r = divmod(n, 58); s = B58[r] + s
    return '1' * (len(b) - len(b.lstrip(b'\0'))) + s
def b58d(s):
    n = 0
    for c in s: n = n * 58 + B58.index(c)
    return b'\0' * (len(s) - len(s.lstrip('1'))) + n.to_bytes((n.bit_length() + 7) // 8, 'big')
# ed25519 on-curve test, needed to derive a program address (a PDA must NOT be a valid curve point)
_P = 2 ** 255 - 19; _D = (-121665 * pow(121666, -1, _P)) % _P
def on_curve(b):
    y = int.from_bytes(b, 'little') & ((1 << 255) - 1)
    if y >= _P: return False
    u, v = (y * y - 1) % _P, (_D * y * y + 1) % _P
    x2 = u * pow(v, -1, _P) % _P
    return pow(x2, (_P - 1) // 2, _P) in (0, 1)
def pda(seeds, program):
    import hashlib
    for bump in range(255, -1, -1):
        h = hashlib.sha256(b''.join(seeds) + bytes([bump]) + b58d(program) + b'ProgramDerivedAddress').digest()
        if not on_curve(h): return b58(h)
    raise SystemExit('no PDA')

mint = sys.argv[1].strip(); buy = sys.argv[2].strip() if len(sys.argv) > 2 else ''
pool = quote = curve = ''

def check_curve(addr):
    info = rpc('getAccountInfo', [addr, {'encoding': 'base64'}])['value']
    if not info or info['owner'] != PUMP: return False
    d = base64.b64decode(info['data'][0])
    vT, vS, rT, rS, sup = struct.unpack_from('<5Q', d, 8)
    print(f'pump.fun curve {addr}\n  virtualSol {vS / 1e9:.3f}  price {(vS / 1e9) / (vT / 1e6):.4g} SOL  mcap {(vS / 1e9) / (vT / 1e6) * sup / 1e6:.1f} SOL  complete {d[48]}')
    return True

pairs = get(f'https://api.dexscreener.com/tokens/v1/solana/{mint}')
if pairs:
    p = sorted(pairs, key=lambda x: -((x.get('liquidity') or {}).get('usd') or 0))[0]
    print('DexScreener OK:', p['baseToken']['symbol'], 'mcap', p.get('marketCap') or p.get('fdv'), 'dex', p.get('dexId'))
    if p.get('dexId') == 'pumpfun' and check_curve(p['pairAddress']): curve = p['pairAddress']
elif check_curve(pda([b'bonding-curve', b58d(mint)], PUMP)):
    print('DexScreener: not indexed yet, but the pump.fun bonding curve exists on-chain')
    curve = pda([b'bonding-curve', b58d(mint)], PUMP)
else:
    print('DexScreener: not indexed → looking for a LaunchLab pool on-chain')
    sigs = rpc('getSignaturesForAddress', [mint, {'limit': 1000}])
    if not sigs: sys.exit('mint has no transactions yet')
    for s in reversed(sigs):                                   # oldest first: the pool is created in the first tx
        tx = rpc('getTransaction', [s['signature'], {'encoding': 'jsonParsed', 'maxSupportedTransactionVersion': 1}])
        if not tx: continue
        keys = [k['pubkey'] for k in tx['transaction']['message']['accountKeys']]
        if LAUNCHLAB not in keys: continue
        infos = rpc('getMultipleAccounts', [keys, {'encoding': 'base64'}])['value']
        for k, info in zip(keys, infos):
            if not info or info['owner'] != LAUNCHLAB: continue
            d = base64.b64decode(info['data'][0])
            if len(d) < 300 or b58(d[205:237]) != mint: continue
            pool, quote = k, b58(d[237:269])
            u = lambda o: struct.unpack_from('<Q', d, o)[0]
            decA, decB = d[18], d[19]; supply = u(21) / 10 ** decA; vA, vB, rA, rB = u(37), u(45), u(53), u(61)
            price_q = ((vB + rB) / 10 ** decB) / ((vA - rA) / 10 ** decA)
            qp = get(f'https://api.dexscreener.com/tokens/v1/solana/{quote}')
            q_usd = float(sorted(qp, key=lambda x: -((x.get('liquidity') or {}).get('usd') or 0))[0]['priceUsd']) if qp else 0
            print(f'LaunchLab pool {pool}\n  quote {quote} (${q_usd})\n  status {d[17]}  price {price_q:.6g} quote/token  mcap ${price_q * supply * q_usd:,.0f}')
            break
        if pool: break
    if not pool: sys.exit('no LaunchLab pool found for this mint — send me the launchpad name')

cfg = open('config.js').read()
cfg = re.sub(r"mint: '[^']*'", f"mint: '{mint}'", cfg)
cfg = re.sub(r"pool: '[^']*'", f"pool: '{pool}'", cfg)
cfg = re.sub(r"quote: '[^']*'", f"quote: '{quote}'", cfg)
cfg = re.sub(r"curve: '[^']*'", f"curve: '{curve}'", cfg)
if buy: cfg = re.sub(r"buy: '[^']*'", f"buy: '{buy}'", cfg)
open('config.js', 'w').write(cfg)
print('config.js updated:', {'mint': mint, 'pool': pool, 'quote': quote, 'curve': curve, 'buy': buy or '(pump.fun default)'})
