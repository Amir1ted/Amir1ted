# AMIR Profile — Clean Install

This package is designed to replace the contents of `Amir1ted/Amir1ted` completely.

## 1. Delete the old profile files

Keep the GitHub repository itself, but delete the previous README, assets, scripts, generated 3D files and old workflow files.

## 2. Copy this package into the repository root

The repository root must look exactly like this:

```text
Amir1ted/
├── README.md
├── SETUP.md
├── .gitignore
├── assets/
│   ├── connect.svg
│   ├── contribution-graph.svg
│   ├── contribution-snake.svg
│   ├── divider.svg
│   ├── footer.svg
│   ├── github-stats.svg
│   ├── header.svg
│   ├── identity.svg
│   ├── neural-skill-atlas.svg
│   └── tech-stack.svg
├── profile-3d-contrib/
│   ├── profile-night-view.svg
│   └── profile-season-animate.svg
├── scripts/
│   ├── generate_profile_data.py
│   └── monochrome_3d.py
└── .github/
    └── workflows/
        └── refresh-profile.yml
```

## 3. Commit and push

```bash
git add -A
git commit -m "feat: rebuild monochrome gothic profile"
git push origin main
```

The single **Refresh Monochrome Profile** workflow is configured to run automatically on that first push.

## 4. What the workflow does

One workflow generates everything sequentially and commits it once, avoiding concurrent workflow push conflicts:

1. Generates live `assets/github-stats.svg`
2. Generates live `assets/contribution-graph.svg`
3. Generates the black/white `assets/contribution-snake.svg`
4. Generates the 3D contribution views
5. Converts the selected 3D views to grayscale
6. XML-validates every generated SVG
7. Commits all dynamic files in one commit

## 5. If the workflow cannot push

Open:

`Repository → Settings → Actions → General → Workflow permissions`

Select **Read and write permissions**, save, then go to **Actions → Refresh Monochrome Profile → Run workflow**.

## 6. First-run behavior

Before the workflow finishes, every dynamic section already has a valid designed **FIRST SYNC PENDING** placeholder. Nothing should appear as a broken image.

No custom token is required for public profile data; the workflow uses GitHub's built-in `GITHUB_TOKEN`.
