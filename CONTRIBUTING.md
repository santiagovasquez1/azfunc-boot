## GitFlow (repo policy)

### Protected branches

- `main`: no direct pushes; changes must go through Pull Requests.
- `develop`: no direct pushes; changes must go through Pull Requests.

### Branches

- `feature/*`: branch from `develop`, PR into `develop`.
- `hotfix/*`: branch from `main`, PR into `main`, then PR (back-merge) into `develop`.
- `release/*`: branch from `develop`, PR into `main`, then PR (back-merge) into `develop`.

### Required checks

This repo includes a GitHub Actions workflow `GitFlow PR Guards` that enforces:

- PRs to `main` must come from `hotfix/*`.
- PRs to `develop` must come from `feature/*`, `release/*`, or `hotfix/*`.

To enforce it, configure Branch Protection for `main` and `develop` and mark this workflow as a required status check.
