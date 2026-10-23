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

