# jeanis.fun

A gentleman whose length is the market cap. Live. Static site: `index.html` + `config.js`, no build step.

## Configure
Edit `config.js`:
- `mint` – contract address (empty = "waiting to launch")
- `chain` – dexscreener chain id (`solana`, `ethereum`, `base`, `bsc` …)
- `name`, `ticker`, `buy` – branding / buy link (default: pump.fun/coin/<mint>)
- `model` – optional `/assets/man.glb` to swap in a real 3D model

## Preview
    python3 -m http.server 8787
    open http://localhost:8787/?mc=165000     # any market cap
    open http://localhost:8787/?ca=<MINT>     # live data for any token

## Deploy (Hostinger)
1. hPanel → Websites → Manage → File Manager → `public_html`
2. Upload `index.html`, `config.js`, `assets/` (delete Hostinger's default index files first)
3. Point `jeanis.fun` at the hosting (Domains → DNS) and enable SSL (Security → SSL)

Any static host works the same way (Vercel/Netlify/Cloudflare Pages: drag the folder in).
