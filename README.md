# Introduction to Machine Learning

Course site and materials for **Phase 1 of the Tahakom AI Early Careers
Program**, delivered by KAUST Academy at KAUST: five days, all participants.

**Site:** <https://kaust-academy.github.io/2026_Tahakom_Introduction_to_Machine_Learning/>

| Day | Topic |
|---|---|
| 1 | Model Development, Evaluation, and Experimentation |
| 2 | Neural Network Foundations and Reproducible Development |
| 3 | Deep Learning Architectures |
| 4 | Reinforcement Learning |
| 5 | Responsible AI and MLOps Foundations |

Generated from
[`Course_Website_Template`](https://github.com/KAUST-Academy/Course_Website_Template).

**The website is generated from one file.** You edit [`course.toml`](course.toml),
run `python3 build.py`, and every page is rebuilt. There is no HTML to
hand-edit, and hand-editing it is always wrong — the next build overwrites it.

---

## Where the material comes from

The decks and notebooks are copied, with unchanged file names, from
`Phase_1_Introduction_to_Machine_Learning/` in the
[`Tahakom_Early_Careers`](https://github.com/KAUST-Academy/Tahakom_Early_Careers)
repository, which holds the LaTeX sources and the day plans. Change a deck or
notebook there first, then copy it here:

| `Tahakom_Early_Careers` | This repo |
|---|---|
| `Day_N_<Title>/Lectures/` | `Slides/Day_N/` |
| `Day_N_<Title>/Labs/` | `Labs/Day_N/` |
| `Day_N_<Title>/Optional/Lectures/` | `Slides/Day_N/Optional/` |
| `Day_N_<Title>/Optional/Labs/` | `Labs/Day_N/Optional/` |

Files are numbered in teaching order within each day. Optional material is
listed on its day's page, marked *Optional*.

Adding or replacing a file is: drop it in, add or update its entry in
[`course.toml`](course.toml), run `python3 build.py --check`, commit, push.
The rest of this file is the template's manual.

---

## Repository layout

```
.
├── course.toml                 # ALL content: days, topics, resources. The only file most people touch.
├── build.py                    # the generator. Standard library only — no pip install.
├── requirements.txt            # the lab environment students install
├── OFFLINE.md                  # classroom delivery runbook (no internet)
├── theme/                      # the KAUST Academy theme. Copied to _site/assets/.
│   ├── css/style.css           #   ported verbatim from the existing course sites
│   ├── img/                    #   logo
│   └── vendor/                 #   bootstrap + the two icon fonts the markup uses
├── Slides/Day_N/               # lecture PDFs, committed  (empty in the template)
├── Labs/Day_N/                 # Jupyter notebooks, committed  (empty in the template)
├── Extra/                      # optional references
├── _site/                      # BUILT OUTPUT — git-ignored, never commit
├── dist/                       # offline bundles — git-ignored, never commit
└── .github/workflows/pages.yml # build + link-check on every push and PR; deploy when enabled
```

Design rules worth knowing before you change anything:

- **Content and presentation are separate.** `course.toml` holds what the
  course *is*; `theme/` holds what it *looks like*.
- **Every emitted path is relative.** That is what lets the identical output
  tree work on GitHub Pages *and* off a USB stick. Never introduce a
  leading-`/` path.
- **No CDN and no network at build time.** Bootstrap and the icon fonts are
  vendored. Offline delivery is a hard requirement for these courses, so
  nothing may be fetched at page load.
- **The theme matches the other course sites.** Same class names
  (`icon-box`, `custom-table`, `table-btn`, `breadcrumbs`), byte-identical
  `style.css`. Restyle by editing the CSS, not the generator.

---

## Requirements

- **Python 3.11 or newer.** That's it.

`build.py` imports only `argparse`, `html`, `shutil`, `sys`, `zipfile`,
`pathlib`, `urllib.parse` and `tomllib` — all standard library. There is
deliberately no `pip install` step, no Ruby and no Node, because the people
maintaining these repos are often on managed laptops without admin rights.

3.11 is the floor because `tomllib` landed there. Check with `python3 -V`.

---

## Building

```bash
python3 build.py              # build _site/
python3 build.py --check      # build, then verify every link resolves  <- use this one
python3 build.py --offline    # build, check, then zip a USB-ready bundle into dist/
python3 build.py --serve      # build, then serve on http://localhost:8000
python3 build.py --help
```

`--check` is what CI runs. It exits non-zero and names the offender:

```
links: 12 ready, 6 coming soon
  orphan (in repo, not on any page): Slides/Day_2/Old_Draft.pdf
  BROKEN: Day 1: 'Foundations' -> missing file Slides/Day_1/Foundations.pdf

1 broken link(s).
```

| Report | Means | Fails the build? |
|---|---|---|
| `BROKEN` | a page links to a file that does not exist | **yes** |
| `orphan` | a file is in the repo but no page links to it | no — a warning |

Orphans are usually a deck you forgot to list, or a superseded draft you forgot
to delete.

`--serve` is closest to how Pages behaves; double-clicking `_site/index.html`
is closest to how the classroom will. **Test both.**

---

## How a page is assembled

1. `build.py` reads `course.toml` with `tomllib`.
2. For each `[[days]]` entry it renders one `<slug>.html`, plus `index.html`
   and `extra.html`.
3. `theme/` is copied to `_site/assets/`.
4. `Slides/`, `Labs/` and `Extra/` are copied into `_site/` verbatim — so the
   PDFs and notebooks travel with the HTML, and Pages and the USB bundle are
   literally the same tree. There is no separate "offline build" that can drift.
5. A `.nojekyll` file is written so Pages serves the output as-is.

Everything from `course.toml` is escaped with `html.escape` on the way out, so
an ampersand in a lecture title cannot break the page.

---

## Adding things

### A lecture deck

Drop the PDF in `Slides/Day_N/`, then:

```toml
  [[days.resources]]
  name   = "Loss functions and linear regression"
  detail = "Squared error, the normal equation, and why regularization helps"
  kind   = "slides"
  file   = "Slides/Day_2/Linear_Models.pdf"
  status = "ready"
```

`file` is relative to the repo root. Rebuild with `--check` to confirm.

### A lab notebook

```toml
  [[days.resources]]
  name   = "Lab 1: Regression"
  detail = "Fit, regularize and tune a model against a sensible baseline"
  kind   = "lab"
  file   = "Labs/Day_2/Lab1_Regression.ipynb"
  colab  = "https://colab.research.google.com/github/KAUST-Academy/<repo>/blob/main/Labs/Day_2/Lab1_Regression.ipynb"
  status = "ready"
```

`kind = "lab"` labels the button **Notebook**; anything else labels it **Open**.

`colab` is **optional and secondary**. It needs internet, and these courses are
delivered offline, so the local notebook is the path that works in the room.
Never make Colab the only route to a lab.

Colab URL pattern:
`https://colab.research.google.com/github/<owner>/<repo>/blob/<branch>/<path>`.
Spaces must be `%20`, which is why folders here use underscores.

### Material that isn't ready yet

Leave `status = "todo"` and omit `file`. The row renders greyed out as
*"Coming soon"*, is not linked, and is skipped by `--check`.

### A new day

Add a `[[days]]` block. Order in the file is the order on the site; the nav and
the home page cards follow automatically.

`icon` is a [Remix Icon](https://remixicon.com) class. Only classes in the
shipped font render — check first, because a missing one renders as a blank box
and `--check` will not catch it:

```bash
grep '^\.ri-flask-line:before' theme/vendor/remixicon/remixicon.css
```

### Changing the look

`theme/css/style.css`, byte-identical to the existing course sites. Brand
colours are custom properties at the top:

```css
--primary-navy: #00264c;  --accent-orange: #f0b500;  --accent-teal: #1bc5c9;
```

**Restyling here does not propagate.** Each course repo carries its own copy,
so a change made in one course will not reach the others, or this template.
That is the remaining duplication in this setup, and it is deliberate —
vendoring keeps every repo self-contained and offline-safe.

Only the files the markup references are vendored (~960 KB): `bootstrap.min.css`,
`remixicon`, `bootstrap-icons`. The sites this was ported from shipped 13 MB —
the rest was source maps, RTL and unminified builds, plus `boxicons`, `swiper`,
`animate.css`, `aos` and `purecounter`, which no page ever loaded.

---

## Offline delivery

**These courses are delivered with no usable internet in the room.** Read
[`OFFLINE.md`](OFFLINE.md) before you travel — the USB bundle, the pre-built
pip wheelhouse for installing PyTorch with `--no-index`, and a pre-flight
checklist to run with Wi-Fi switched off.

```bash
python3 build.py --offline      # -> dist/<Course>_offline.zip
```

Unzip, double-click `index.html`. No server, no internet.

---

## Deployment

`.github/workflows/pages.yml` runs on every push and pull request to `main`:

1. `python3 build.py --check` — **a broken link fails the build before it can
   reach the site.**
2. `python3 build.py --offline` — the bundle is uploaded as a workflow
   artifact, so you can download the exact bundle for any commit for 90 days.
3. Deploys `_site/` to GitHub Pages — **only when enabled**, see below.

### Turning the site on — two independent switches

| Switch | Where | Why |
|---|---|---|
| Repo **public** | Settings → General → Change visibility | Pages on the org's free plan requires it |
| `DEPLOY_PAGES` = `true` | Settings → Secrets and variables → Actions → Variables | Un-skips the deploy job |

While the repo is private the deploy job is **skipped**, so CI stays green and
reflects real problems only. The offline bundle still builds on every push.

Nothing else is needed — the workflow enables Pages itself. You do not have to
visit Settings → Pages.

> Going private again **unpublishes** the site and disables Pages. Flipping
> public briefly does not retract anything either: in that window the repo can
> be cloned, forked and indexed, and public repo events are archived by third
> parties. Decide once, per course.

---

## Naming conventions

| Thing | Convention | Example |
|---|---|---|
| Repo | `<year>_<Client>_<Course>` | `2026_Tahakom_Introduction_to_Machine_Learning` |
| Day folders | `Day_N`, **underscores, never spaces** | `Slides/Day_3/` |
| Slide PDFs | `Title_Case_With_Underscores.pdf` | `Neural_Networks.pdf` |
| Lab notebooks | `LabN_Topic.ipynb` | `Lab2_Backpropagation.ipynb` |
| Solutions | same name + `_Solution` | `Lab2_Backpropagation_Solution.ipynb` |
| Day slugs | lowercase, URL-safe | `day3` |

Spaces in paths are the most common source of broken Colab links — they need
`%20`, and it is routinely forgotten. Underscores avoid the whole class of bug.
Existing course repos are inconsistent about this; new ones should not be.

---

## Commit convention

Follow [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/):
`<type>(<scope>): <description>`, imperative mood.

```
feat(day2): add Ridge and Lasso deck
fix(day1): correct dataset path in the leakage notebook
docs(offline): document the wheelhouse build for Windows
chore(theme): bump bootstrap
```

| Type | Use for |
|---|---|
| `feat` | new slides, notebooks, days |
| `fix` | corrections to existing material |
| `docs` | README, OFFLINE, comments |
| `chore` | build script, CI, theme, dependencies |

---

## Known quirks carried over

The theme is a faithful port, so it carries a few oddities from the original
sites. They are harmless, and left in place so every course site matches:

- **`var(--primary-red)` is never defined.** The "COURSE SCHEDULE" label
  references it, so the declaration is invalid and the text inherits navy.
  Define the token, or drop the declaration, if you want it coloured.
- **The font stack asks for Raleway and Open Sans, neither of which is
  loaded**, so everything renders in the system sans-serif fallback. Bundling
  Raleway locally would fix it — and would make the site look different from
  the others.
- **Day and Extra pages have no footer**, so the copyright and the
  "recording not permitted" notice appear only on the home page. To put it
  everywhere, add `{footer(course)}` back to `render_day` and `render_extra`
  in `build.py`.

---

## Things that will catch you out

- **Editing `_site/` does nothing.** It is deleted and regenerated on every
  build, and it is git-ignored. Edit `course.toml` or `theme/`.
- **Forgetting `[course].repo`** sends every Colab button to whichever repo the
  template last pointed at. Set it first.
- **An `icon` that isn't in the shipped remixicon font renders as a blank
  box.** `--check` does not catch this; grep the CSS first.
- **`status = "ready"` without a `file`** fails `--check`. That is deliberate —
  it is how a half-finished row gets caught.
- **Spaces in filenames** work locally and break Colab links. Use underscores.
- **A notebook that downloads its dataset at runtime will fail in the
  classroom.** Commit the data under `Labs/`.
- **Wheelhouses are platform-specific.** One built on an Apple Silicon Mac will
  not install on a Windows laptop. See `OFFLINE.md`.
- **`.ipynb` files are set `merge=binary`** in `.gitattributes`. Git will not
  auto-merge them, on purpose — a merged notebook is usually corrupt. Resolve
  conflicts by picking one side.
- **Python 3.10 and older will not run the build**, because `tomllib` does not
  exist there. The script says so and exits rather than failing obscurely.

---

## License

GPL-3.0, as with other KAUST Academy course material. Recording and uploading
lectures online is not permitted.
