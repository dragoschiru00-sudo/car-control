# Car Control — How Cars Really Move

An interactive single-page learning resource on vehicle dynamics: weight transfer, the friction circle, braking technique, understeer/oversteer, drifting, and rally craft.

Open `index.html` directly, or visit the GitHub Pages site.

Interactive modules:
- Weight transfer visualiser (4-wheel load distribution)
- Friction circle grip budget
- Stopping-distance calculator across surfaces
- Understeer / oversteer balance simulator
- 2D drift simulator (bicycle model, handbrake, countersteer scoring)
- Pace-note drill and 10-question quiz

All physics is simplified and intended for teaching feel, not engineering.

## Ask-the-tutor (Ollama)

The floating **Ask the tutor** button answers questions about the material using a
local model. A public HTTPS page cannot call `http://localhost:11434`, so run the
bundled host:

```
ollama serve
python serve.py          # http://localhost:8765
```

`serve.py` serves the site and proxies `/api/chat` to Ollama (streaming NDJSON).
Open the page through `serve.py` and the tutor works; the static site keeps working
without it.

To use it from a phone, expose port 8765 with a tunnel, e.g.
`cloudflared tunnel --url http://127.0.0.1:8765`.

## Hosted on the Oracle VM (primary)

Everything runs on the VM (132.145.17.93), so the PC can be off:

- `ollama.service` — Ollama with `llama3.2:3b`
- `carcontrol.service` — `/opt/carcontrol/serve.py` on port 80 (rate limited: 30 questions/hour per IP, one at a time)
- `cctunnel.service` — cloudflared quick tunnel to a public HTTPS URL

Public URL is the trycloudflare one printed by `sudo journalctl -u cctunnel | grep trycloudflare`.

Update the site: `scp index.html ubuntu@132.145.17.93:/tmp/ && ssh ... 'sudo cp /tmp/index.html /opt/carcontrol/'`
(owned by root; `systemctl restart carcontrol`).

Quick tunnel URLs change when the service restarts. For a permanent hostname either add
an OCI Security List rule for TCP 80 (then http://132.145.17.93/ works directly) or use a
named Cloudflare tunnel with a domain.
