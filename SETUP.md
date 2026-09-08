# Setup — AMIR Monochrome Profile v2

1. Copy **all files and folders** from this package into `Amir1ted/Amir1ted` and commit/push to `main`.
2. This version includes placeholder SVGs, so no section should render as a broken image during the first sync.
3. The first push automatically triggers three path-filtered workflows:
   - **Monochrome Profile Data** → generates `assets/github-stats.svg` and `assets/contribution-graph.svg` locally from GitHub GraphQL.
   - **Monochrome Contribution Snake** → replaces the snake placeholder with your live grayscale contribution snake.
   - **Monochrome 3D Contributions** → generates the 3D contribution SVGs and post-processes every generated color into grayscale.
4. Open the **Actions** tab after the push. You should see workflow runs. If Actions are disabled for the repository, enable them; otherwise you can also use **Run workflow** manually.
5. If a workflow can generate the SVG but fails on `git push` with a permissions error, open **Settings → Actions → General → Workflow permissions** and select **Read and write permissions**.
6. Generated commits only touch generated asset paths, while push triggers are limited to workflow/script files, so the workflows do not create an infinite loop.

## Why v2 is more reliable

The previous Stats and Contribution Graph depended on third-party Vercel-hosted image endpoints. v2 removes those dependencies: the repository generates and serves its own SVG files. The only remaining remote images are the small Shields/Komarev badges at the top and in Connect With Me.

## GitHub native contribution calendar

README files cannot restyle the green contribution calendar that GitHub itself renders outside the README. Every contribution visualization **inside** this README is monochrome.
