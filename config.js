// Edit this and redeploy. Nothing else needs to change.
window.PEPE_CONFIG = {
  name: 'jeanis',               // brand in the top-left
  ticker: 'JEANIS',             // "Buy $JEANIS"
  chain: 'solana',              // dexscreener chain id: solana, ethereum, base, bsc ...
  mint: '',                     // contract address. Empty = placeholder market cap below
  buy: '',                      // custom buy link. Empty = pump.fun/coin/<mint>
  placeholderMc: 6000,          // market cap shown while mint is empty
  // On-chain source for launchpad tokens the aggregators haven't indexed yet (Raydium LaunchLab / bonk.fun style pools).
  // pool = the LaunchLab PoolState account, quote = the pool's quote mint (SOL, USD1, PEPE ...). Leave empty to skip.
  pool: '',
  quote: '',
  rpc: 'https://solana-rpc.publicnode.com',
  model: '',                    // optional: '/assets/man.glb' to use a real model instead of the built-in one
  modelScale: 1,                // scale for the optional glb
  modelAnchor: [0, 1.6, 0.2],   // where the member attaches on the optional glb (scene units, after scaling & grounding)
};
