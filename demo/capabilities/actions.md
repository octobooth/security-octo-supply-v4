# GitHub Actions

- **id**: area.actions.workflows
- **product**: GitHub Actions (`product.actions`)

**Capabilities in this group:** `capability.required-workflows`, `capability.reusable-workflows`

---

## Required Workflows

- **id**: capability.required-workflows

Organization/enterprise-enforced workflows that must pass on targeted repositories, defined via rulesets.

### Value Proposal

- Enforce generalized checks across many repositories from a central place — the workflow can live in another repo or even another org in the same enterprise.

### Prestaged content

- `content.octocat-ruleset` — "OD OctoCAT Supply Ruleset".
- `content.dependency-review-workflow` — Workflow defined centrally in [octobooth/octocat-supply-reusable-workflows](https://github.com/octobooth/octocat-supply-reusable-workflows/blob/main/.github/workflows/dependency-review.yml); enforcement requires a separately configured destination ruleset.
- `content.tos-download-pr` — PR that the required check runs on.

### Shown in walkthroughs

- `walkthrough.actions.required-workflows`
- `walkthrough.ghas.dependency-review-license`

## Reusable Workflows

- **id**: capability.reusable-workflows

Reusable workflows standardize CI/CD. This template keeps a local copy of the central build workflow so both services can call it without cross-repository access requirements.

### Value Proposal

- Streamline common CI/CD tasks across an org or enterprise.
- Enforce consistency, reduce duplication, and improve maintainability across many projects.
- Allows for an innersourcing model to CI/CD

### Prestaged content

- `content.build-and-publish-workflow` — `.github/workflows/build-and-publish.yml` calling the local `.github/workflows/build-publish-containers.yml` at the caller's commit.

### Shown in walkthroughs

- `walkthrough.actions.reusable-workflows`
