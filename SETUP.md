# Setup — AMIR Monochrome Gothic Profile

This package is designed for the profile repository `Amir1ted/Amir1ted`.

## Install

1. Copy **all files and folders** from this package into the root of `Amir1ted/Amir1ted`.
2. Commit and push to the `main` branch.
3. Open **Actions** on GitHub and run these workflows once manually:
   - `Monochrome Contribution Snake`
   - `Monochrome 3D Contributions`
4. Refresh your profile after both actions finish.

The included snake and 3D files are placeholders so the README never starts with broken images. The workflows replace them with live contribution visualizations.

## If a workflow cannot push

Go to:

`Repository Settings → Actions → General → Workflow permissions`

and make sure the repository allows **Read and write permissions** for `GITHUB_TOKEN`.

## Design rules

- Pure monochrome: black / white / grayscale only.
- No theme-specific colored logos.
- The activity graph, snake and 3D contribution surface are all intentionally grayscale.
- The native GitHub contribution calendar shown by GitHub itself is outside README control. GitHub does not allow a profile README to inject CSS into the surrounding profile page, so this package cannot recolor those native squares.

## Update your skill levels

Edit `assets/neural-skill-atlas.svg`. Current self-ratings:

| Skill | Level |
|---|---:|
| Python | 5/5 |
| Machine Learning | 5/5 |
| Deep Learning | 4/5 |
| Computer Vision | 3/5 |
| PyTorch | 4/5 |
| OpenCV | 5/5 |
| YOLO | 2/5 |
| Git / GitHub | 3/5 |
| Linux | 2/5 |
| Docker | 4/5 |

## Attribution

The brain silhouette/path data used in `assets/neural-skill-atlas.svg` is based on a public-domain / CC0 human-brain vector from Wikimedia Commons. See `ATTRIBUTION.md`.
