# Submission checklist

Deadline: **Sunday 15 November 2026, 23:59 local time.** Target: submit by 20:00, then review as a judge would.
Feature freeze: Sunday 14:00. Owner of this list: workstream E; everyone reviews.

## Saturday night / Sunday morning

- [ ] Open the Project tab on spaceappschallenge.org and read the submission requirements: required fields, length
      limits, demo format and length. Write them at the top of [submission-text.md](submission-text.md) and trim the
      draft to fit. *(Not done yet: the guide could not be opened from a script.)*
- [ ] Team page: all members joined, challenge "Field Shift: Adapting Farms with NASA Data" selected.
- [x] Repository owner: Settings → Pages → Source: "GitHub Actions". The "Deploy app to GitHub Pages" workflow runs
      green and https://kub147.github.io/PlotWise/ loads on a laptop. *(Still to check on a real phone.)*
- [x] Repository is public.

## App, after the feature freeze

- [ ] `cd app && npm run build` passes on a clean clone.
- [ ] Click through all six pages for one Tribune, one Colby and one Hays field. No empty cards, no "undefined".
- [ ] Rotation replay: sliders reorder the ranking; "Reset to equal weights" works; the yield-level switch works.
- [ ] Evidence links on a rotation card open "How we know" at the right entry.
- [ ] Phone width: navigation at the bottom works; wide charts scroll sideways.
- [ ] If the engine was re-run after Saturday 21:00: the three fixed tiles on "How we know" (61%, 45%, failure years)
      still match `docs/engine-validation.md`.

## Honesty review (read every page once with these in mind)

- [ ] Nowhere does the app or the text say that rain is declining.
- [ ] Net return is always presented as a comparison between rotations, never as farm profit.
- [ ] No rotation is called "the best" without the priorities caveat.
- [ ] Missing data shows as missing (Colby and Hays have no aerial photo and no heat image).
- [ ] The "This season" page makes no forecast.

## Submission form

- [ ] Project name, short summary and detailed description pasted from [submission-text.md](submission-text.md),
      with every `[SQUARE BRACKET]` placeholder filled in.
- [ ] Demo link is public and plays without logging in. Recorded from [demo-storyboard.md](demo-storyboard.md).
- [ ] Repository link and live app link.
- [ ] Space agency data and references pasted from [data-and-references.md](data-and-references.md).
- [ ] The question on the use of AI is answered accurately by the whole team.
- [ ] Limits stated (project brief, section 9; "What we do not claim" in the app).
- [ ] Someone outside the team opened the live app and used it without explanation.

## After submitting

- [ ] Open the submitted project page in a private browser window and follow every link.
- [ ] Fix only typos and broken links before 23:59.
