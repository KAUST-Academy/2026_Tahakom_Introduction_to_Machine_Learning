# Offline classroom delivery

Assume the room has no usable internet. Everything below works with the network
cable unplugged. Test it that way before you travel.

---

## 1. Build the bundle

On a machine that *does* have the material:

```bash
python3 build.py --offline
```

This produces `dist/<Course>_offline.zip`, containing the
whole site plus every slide PDF and lab notebook.

It refuses to build if any page links to a file that is missing, so a bundle
that exists is a bundle whose links all work.

## 2. Hand it out

Copy the zip to a USB stick, one per table. Students unzip it anywhere and
**double-click `index.html`**.

No web server, no internet, no install. Every path the site emits is relative,
so the browser resolves it straight off the filesystem via `file://`. There is
no JavaScript — the mobile menu is a CSS checkbox — so nothing is blocked by
`file://` origin rules.

If you prefer to serve it over the room's LAN instead:

```bash
cd <Course> && python3 -m http.server 8000
```

Students then browse to `http://<your-laptop-ip>:8000`.

## 3. The labs

Clicking **Notebook** downloads the `.ipynb`. Students open it in Jupyter:

```bash
cd <Course>
jupyter lab
```

The **Colab** button is deliberately secondary — it needs internet. Offline, the
local notebook is the path that works.

### Getting the Python environment onto laptops with no internet

Do this **before** the course, on a machine with internet, matching the
students' OS and Python version:

```bash
# 1. Download every wheel into a folder
pip download -r requirements.txt -d wheelhouse

# 2. Ship `wheelhouse/` on the USB stick alongside the bundle

# 3. In the classroom, on each laptop:
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install --no-index --find-links=wheelhouse -r requirements.txt
```

`--no-index` is what forces pip to never reach for the network. If it can't
satisfy a requirement from `wheelhouse/`, it fails loudly instead of hanging.

**Wheels are platform-specific.** A wheelhouse built on an Apple Silicon Mac
will not install on Windows. If the room is mixed, build one wheelhouse per
platform (`pip download --platform ...`), or standardise the laptops.

Budget roughly 2–3 GB for a wheelhouse with PyTorch. Check the stick has room.

### Datasets

Any dataset a lab uses must be in the repo under `Labs/`, not fetched at
runtime. A notebook whose first cell is `pd.read_csv("https://...")` will fail
in the classroom. Keep them small enough to commit; if one is genuinely large,
it does not belong in the course.

---

## Pre-flight checklist

Run through this the day before, on a laptop with **Wi-Fi turned off**:

- [ ] `python3 build.py --check` passes
- [ ] Unzip the bundle somewhere fresh and open `index.html` by double-click
- [ ] Every day page loads; logo and styling appear
- [ ] Open one slide PDF from each day
- [ ] Open one notebook from each day and **run it top to bottom**
- [ ] No cell reaches for the network
- [ ] Install the wheelhouse into a clean venv on a spare laptop
- [ ] Spare USB sticks prepared

## Known limits

- **Colab buttons will not work.** That is expected; they are the online path.
- **PDF rendering** relies on the browser's built-in viewer. Chrome, Edge,
  Firefox and Safari all have one.
- **`file://` and PDFs**: a few locked-down enterprise browser policies block
  local PDF rendering. If the participants' managed laptops do that, use the
  `python3 -m http.server` route instead, which sidesteps it.
