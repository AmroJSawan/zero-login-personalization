# Zero-Login Personalization

Engineering reference for personalizing large portals when the visitor has no account, no
login, and no persistent identifier. Domain-agnostic.

| Page | Source |
|---|---|
| Live signal surface (interactive) | `index.html` |
| Reference architecture | `ARCHITECTURE.md` |
| Model selection guide (verified survey) | `MODEL-SELECTION.md` + `MODEL-SELECTION-verifier-log.json` |
| Inference and prediction targets | `PREDICTION.md` |
| Temporal layer and adaptation evidence | `ADAPTATION.md` |
| Signal-to-model stack | `MODELS.md` |

## Build

```bash
python3 build-site.py   # pure stdlib, emits site/
```

Serve `site/` with any static file server. `.github/workflows/pages.yml` builds and
deploys to GitHub Pages on every push to `main`.

## Provenance

The model selection guide is the synthesis of a twelve-agent research survey: 108 models
across nine families, 76 claims adversarially verified against primary sources, 29 flagged.
Every number in it is tagged `[V]` verified, `[C]` corrected, or `[U]` unconfirmed, and the
raw verifier log ships alongside it. The signal surface page transmits nothing: every value
it shows is computed locally in the viewer's browser.
