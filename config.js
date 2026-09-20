// Edit this and redeploy. Nothing else needs to change.
window.PEPE_CONFIG = {
  name: 'bowlcut',              // brand in the top-left  (TODO: final name)
  ticker: 'BOWL',               // "Buy $BOWL"            (TODO: final ticker)
  chain: 'solana',              // dexscreener chain id: solana, ethereum, base, bsc ...
  mint: 'CZ3qbW9qwENcoBfv5b4sNcbhvziWu4o2LbNP4BEibCHq',                     // contract address. Empty = placeholder market cap below
  buy: '',                      // custom buy link. Empty = pump.fun/coin/<mint>
  placeholderMc: 6000,          // market cap shown while mint is empty
  // On-chain source for launchpad tokens the aggregators haven't indexed yet (Raydium LaunchLab / bonk.fun style pools).
  // pool = the LaunchLab PoolState account, quote = the pool's quote mint (SOL, USD1, PEPE ...). Leave empty to skip.
  pool: '8S5SLQ5PdBer3Zbh5ysyZF1QC1qgZcjoiibFopH2FG4e',
  quote: 'PEPEqnuuCDbBC89p1u9vpnP1KQ2oj1xTcQBsjt9X55m',
  rpc: 'https://solana-rpc.publicnode.com',
  model: '',                    // optional: '/assets/man.glb' to use a real model instead of the built-in one
  modelScale: 1,                // scale for the optional glb
  modelAnchor: [0, 1.6, 0.2],   // where the member attaches on the optional glb (scene units, after scaling & grounding)
};
