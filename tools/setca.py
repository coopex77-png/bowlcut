#!/usr/bin/env python3
"""Point the site at a new mint. Usage: tools/setca.py <MINT> [buy_url]
Checks DexScreener; if the token isn't indexed, finds its Raydium LaunchLab pool on-chain (via the mint's first
transaction), verifies the layout, reads the quote mint, and writes mint/pool/quote into config.js."""
import json, re, struct, sys, base64, time, urllib.request

RPCS = ['https://api.mainnet-beta.solana.com', 'https://solana-rpc.publicnode.com']
LAUNCHLAB = 'LanMV9sAd7wArD4vJFi2qDdfnVhFxYSUg6eADduJ3uj'
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

mint = sys.argv[1].strip(); buy = sys.argv[2].strip() if len(sys.argv) > 2 else ''
pool = quote = ''

pairs = get(f'https://api.dexscreener.com/tokens/v1/solana/{mint}')
if pairs:
    p = sorted(pairs, key=lambda x: -((x.get('liquidity') or {}).get('usd') or 0))[0]
    print('DexScreener OK:', p['baseToken']['symbol'], 'mcap', p.get('marketCap') or p.get('fdv'), 'dex', p.get('dexId'))
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
if buy: cfg = re.sub(r"buy: '[^']*'", f"buy: '{buy}'", cfg)
open('config.js', 'w').write(cfg)
print('config.js updated:', {'mint': mint, 'pool': pool, 'quote': quote, 'buy': buy or '(pump.fun default)'})
