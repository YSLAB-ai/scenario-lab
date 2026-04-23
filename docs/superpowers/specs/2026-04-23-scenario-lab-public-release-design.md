# Scenario Lab Public Release Design

Date: 2026-04-23

## Summary

Prepare the repository for a user-first public release under the product name `Scenario Lab`, with the GitHub repository renamed to `scenario-lab` and the repo content rewritten around an experimental-preview experience instead of an internal engineering handoff.

The release should make a first-time visitor understand:

- what Scenario Lab does
- how to run one local demo quickly
- how to use it in natural language through Codex or Claude
- what the current limitations are

The release should also update the GitHub-facing presentation layer:

- repository description
- homepage
- topics
- social preview image

This is a public-preview packaging pass, not a core-model redesign.

## Verified Current State

The current repository state is not public-release-shaped:

- `README.md` is status-heavy and oriented toward accepted internal repo state rather than first-time public users.
- Install guides exist for Codex and Claude, but there is no public quickstart, public demo walkthrough, or user-first documentation map.
- The repository currently lives at `git@github.com:YSLAB-ai/HeuristicSearchEngine.git`.
- The packaged runtime and local adapter bundles already exist and are verified to produce end-to-end reports.

These facts make the repo usable for a technical reviewer, but not yet shaped like a public landing page.

## Audience And Positioning

### Primary Audience

The public release should target end users first:

- users who want to run scenario analysis
- users who may not want to read much code before trying the system

Builder-facing material should still exist, but it should not dominate the homepage.

### Product Posture

The release should present the repo as an `experimental preview`.

That means:

- clear value proposition
- real, runnable demos
- honest limitations
- no production-readiness language

## Naming

### Public Product Name

The public product name should be:

- `Scenario Lab`

### GitHub Repository Name

The GitHub repository should be renamed to:

- `scenario-lab`

### Internal Names

Internal package and module names do not need to be renamed in this pass unless they create obvious user confusion. This keeps the public-release scope bounded and avoids unnecessary churn in the codebase.

## Trademark Boundary

The naming decision is based on a preliminary federal screening only.

Verified facts:

- an exact USPTO combined-mark query for `CM:"Scenario Lab"` returned `No results found`
- a broad USPTO wordmark search for `"Scenario Lab"` returned `8,044` results

This is enough for a preliminary naming screen, but not enough to claim legal clearance. Public-release materials should not state or imply that the name has been legally cleared.

## Release Approach

### Option 1: Minimal Polish

- rewrite `README.md`
- add a quickstart
- set GitHub metadata

Pros:

- fastest
- lowest change surface

Cons:

- still feels like an internal repo with a nicer front page
- weak public impression

### Option 2: Public Preview Relaunch

- rewrite the repo around `Scenario Lab`
- make the homepage user-first
- add one-command demo and natural-language walkthrough
- add public docs and visual assets
- update GitHub-facing metadata

Pros:

- matches the desired public posture
- gives end users a clear first-use path
- keeps scope bounded

Cons:

- larger doc and presentation pass

### Option 3: Full Marketing Pass

- heavy branding
- polished visuals everywhere
- deeper narrative content

Pros:

- strongest launch surface

Cons:

- over-scoped for the current repo state
- risks overpromising

### Selected Approach

Use `Option 2: Public Preview Relaunch`.

It matches the desired audience and posture without pretending the repo is a finished product.

## Public Surface Design

### Top-Level README

`README.md` should become the public homepage and lead with `Scenario Lab`.

Required structure:

1. Hero
   - `Scenario Lab`
   - short value proposition
   - `Experimental preview` label

2. What It Does
   - plain-language bullets
   - no architecture-heavy opening

3. Quickstart
   - one-command local demo first
   - expected output shown directly below

4. Natural-Language Workflow
   - copyable example prompts
   - Codex and Claude paths linked

5. Public Demo
   - `U.S.-Iran` end-to-end example
   - short report excerpt or artifact screenshot

6. Install Paths
   - Codex
   - Claude
   - deeper docs linked rather than embedded in full

7. What’s Included In This Preview
   - replay library
   - calibrated confidence
   - local adapters
   - domain synthesis
   - ingestion support

8. Current Limits
   - explicit and honest
   - includes the deferred OCR note
   - includes the evidence-pack/domain-knowledge dependency and community-improvement model

9. Minimal Builder Section
   - short repo layout
   - short development link-outs

The homepage should optimize for first-use comprehension, not for completeness.

### Public Docs Map

Add or rewrite these public-facing docs:

- `docs/quickstart.md`
- `docs/natural-language-workflow.md`
- `docs/demo-us-iran.md`
- `docs/limitations.md`
- `docs/release-notes/public-preview.md`

The public docs should be short, readable, and linked directly from `README.md`.

### Internal Docs Segregation

Internal status and planning material should remain in the repo, but it should be clearly separated from the public path.

This can be done by:

- keeping internal material under existing status/spec/plan areas
- reducing direct homepage emphasis on those areas
- optionally adding a short line in the README noting that detailed internal status notes remain in `docs/status`

The public landing surface should not read like a changelog.

## Demo Design

### Primary Public Example

The public example should use:

- `U.S.-Iran`

Verified basis:

- current news coverage confirms that U.S.-Iran developments are a timely public topic as of April 2026

### Demo Content

The demo should show:

1. starting a run
2. drafting or saving intake
3. drafting evidence
4. approving and simulating
5. generating a report

It should also show natural-language prompts such as:

- `Start a U.S.-Iran scenario run for the next 30 days`
- `Draft the evidence packet`
- `Approve and simulate`
- `Update the run with a new Strait of Hormuz development`

### Demo Verification Rule

All demo commands and report excerpts must come from real verified outputs in the repo’s current accepted state. No fabricated screenshots, fake metrics, or invented report text.

## Visual Assets

### Required Assets

The release should include:

- one social preview image for GitHub
- at least one polished README visual that helps explain the product quickly

### Visual Style

The design should feel like an experimental analysis product, not like a generic OSS README.

Desired qualities:

- clear product name
- local-first and natural-language emphasis
- visible workflow shape
- readable at GitHub preview size

### Asset Sources

Visuals may be created with image generation, but they must still represent the product honestly. They should not imply capabilities the repo does not have.

## GitHub-Facing Metadata

### Repository Rename

The repository should be renamed from `HeuristicSearchEngine` to `scenario-lab`.

Verified GitHub behavior:

- GitHub supports repository renaming
- old web and git URLs are redirected after rename
- local clones should still update their `origin` URL

Because the rename changes a live public-facing GitHub surface, it should be treated as a final action-time step after the repo content is ready.

### Description

Use a description along the lines of:

- `Experimental local-first scenario analysis for natural-language forecasting with Codex or Claude`

### Topics

Initial topic set:

- `scenario-analysis`
- `forecasting`
- `decision-support`
- `local-first`
- `codex`
- `claude`
- `mcts`
- `agent-tools`

### Homepage

If no dedicated site exists yet, the homepage can point to the repository itself or to the primary public docs target once finalized.

### Social Preview

Set the repo social preview to the generated `Scenario Lab` preview asset.

## Limitations Messaging

The limitations section should be explicit about model quality.

Required points:

- output quality depends heavily on the approved evidence packet
- output quality depends heavily on the depth and quality of the domain pack
- replay calibration is stronger in some domains than others
- the system is designed to improve over time through community contributions and protected domain-evolution workflows
- this is an experimental preview, not a production forecasting guarantee
- OCR-backed PDF ingestion remains deferred

This messaging should appear in both:

- `README.md`
- `docs/limitations.md`

## Implementation Sequence

1. Create the public-release branch/workspace.
2. Rewrite `README.md` into the new public homepage.
3. Add the public docs set.
4. Verify and capture a real `U.S.-Iran` demo path from current repo behavior.
5. Create the visual assets.
6. Update local adapter bundle READMEs so they match the public release language.
7. Prepare the GitHub-facing metadata update package.
8. After the repo content is verified, perform the live GitHub rename and metadata edits as the final action-time step.
9. Run verification on the changed docs/demo commands.
10. Do a final public-surface pass for clarity and consistency.

## Success Criteria

The public-release pass is complete when:

- the repo reads as `Scenario Lab` to a first-time visitor
- `README.md` is user-first rather than status-first
- the public docs set exists and is internally consistent
- the `U.S.-Iran` demo is real and verified
- the limitations section honestly explains evidence/domain dependence and community contribution
- the visual assets are committed and used
- the local Codex and Claude paths are clearly documented for first use
- the GitHub metadata package is prepared and the live rename/metadata edits are ready as the final public-facing step

## Non-Goals

This pass does not:

- rename the internal Python package unless later proven necessary
- redesign the core simulation engine
- claim legal clearance of the `Scenario Lab` name
- remove internal status docs from the repository
- implement OCR-backed PDF ingestion

## Risks And Controls

### Risk: Overpromising

Control:

- keep `Experimental preview` language visible
- maintain an honest limitations section

### Risk: Public README Still Feels Internal

Control:

- make quickstart and natural-language usage appear before repo-layout or status material

### Risk: Visuals Imply Capabilities The Repo Does Not Have

Control:

- keep visuals workflow-grounded
- only use verified demo outputs and honest product framing

### Risk: Public Metadata Changes Are Hard To Roll Back Socially

Control:

- treat live GitHub description/homepage/topics/social-preview changes as a distinct final action
- treat the GitHub repo rename the same way
- verify all content locally first
