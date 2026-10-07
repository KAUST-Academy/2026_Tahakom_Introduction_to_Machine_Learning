"""Live YOLO compression demo: one detector at different sizes and precisions, on your webcam.

Run it on your own laptop, not on Colab, from this folder:

    pip install -r ../../requirements.txt         once (or: pip install ultralytics onnx onnxruntime onnxslim)
    python yolo_live_demo.py                      webcam 0
    python yolo_live_demo.py --camera 1           another camera (on a Mac, often a nearby iPhone)
    python yolo_live_demo.py --source clip.mp4    a video file instead of a camera
    python yolo_live_demo.py --base s             a smaller base model, for slower laptops

The first run downloads YOLO11 and COCO128 and builds the versions below into yolo_models/ next to
this file, which takes a few minutes; later runs start at once. In the window, keys 1 to 4 switch
version, and q or Esc quits.

    1  YOLO11m, float32         ONNX Runtime on the CPU: the original
    2  YOLO11m, int8            ONNX Runtime on the CPU: quantised, its output head kept in float32 (Lab 1, Part 5)
    3  YOLO11n, float32         ONNX Runtime on the CPU: a smaller architecture, not a distilled YOLO11m
    4  YOLO11m, float16, GPU    PyTorch on Apple's GPU (MPS) or an NVIDIA GPU (CUDA), if the laptop has one

The corner of the window shows the model's time per frame, the whole loop's frames per second, the
file size, and the accuracy (mAP50-95 on COCO128, measured once while building).
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

import cv2
import numpy as np

HERE = Path(__file__).resolve().parent
CACHE = HERE / "yolo_models"
WINDOW = "YOLO compression demo"


def parse_args():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--camera", type=int, default=0, help="camera index (default 0)")
    p.add_argument("--source", help="a video file to use instead of a camera")
    p.add_argument("--base", default="m", choices=["n", "s", "m", "l"], help="base model size (default m)")
    p.add_argument("--small", default="n", choices=["n", "s", "m"], help="the smaller architecture (default n)")
    p.add_argument("--rebuild", action="store_true", help="rebuild the models even if yolo_models/ has them")
    p.add_argument("--skip-map", action="store_true", help="build without measuring accuracy (faster)")
    p.add_argument("--benchmark", type=int, metavar="N", help="time N frames per version, print a table, no window")
    p.add_argument("--snapshot", metavar="DIR", help="save one annotated frame per version to DIR, no window")
    return p.parse_args()


def gpu_device():
    import torch
    if torch.backends.mps.is_available():
        return "mps", "Apple GPU (MPS)"
    if torch.cuda.is_available():
        return 0, "NVIDIA GPU (CUDA)"
    return None, None


def quantize_int8(src, dst, calibration_images):
    """Static int8 quantisation with ONNX Runtime, keeping the detection head's decoding in float32."""
    import onnx
    from onnxruntime.quantization import CalibrationDataReader, QuantFormat, QuantType, quantize_static
    from onnxruntime.quantization.shape_inference import quant_pre_process

    def letterbox(path, size=640):
        image = cv2.imread(str(path))
        h, w = image.shape[:2]
        s = size / max(h, w)
        image = cv2.resize(image, (round(w * s), round(h * s)))
        canvas = np.full((size, size, 3), 114, np.uint8)
        canvas[:image.shape[0], :image.shape[1]] = image
        return (canvas[:, :, ::-1].transpose(2, 0, 1)[None] / 255.0).astype(np.float32)

    class Calibration(CalibrationDataReader):
        def __init__(self):
            self.images = iter([{"images": letterbox(f)} for f in calibration_images])

        def get_next(self):
            return next(self.images, None)

    prepped = str(Path(dst).with_suffix(".prepped.onnx"))
    quant_pre_process(src, prepped)
    head = [n.name for n in onnx.load(prepped).graph.node if n.name.startswith("/model.23/") and n.op_type != "Conv"]
    quantize_static(prepped, dst, Calibration(), quant_format=QuantFormat.QDQ, per_channel=True,
                    activation_type=QuantType.QUInt8, weight_type=QuantType.QInt8, nodes_to_exclude=head)
    original, quantised = onnx.load(src), onnx.load(dst)       # keep the class names YOLO stores in the file
    del quantised.metadata_props[:]
    quantised.metadata_props.extend(original.metadata_props)
    onnx.save(quantised, dst)
    os.remove(prepped)


def build(args):
    """Export, quantise and measure every version; cache the result in yolo_models/summary.json."""
    from ultralytics import YOLO
    from ultralytics.data.utils import check_det_dataset

    summary_path = CACHE / "summary.json"
    if summary_path.exists() and not args.rebuild:
        summary = json.loads(summary_path.read_text())
        if summary.get("base") == args.base and summary.get("small") == args.small:
            return summary["versions"]

    CACHE.mkdir(exist_ok=True)
    here = os.getcwd()
    os.chdir(CACHE)                      # Ultralytics downloads weights into the working folder
    try:
        print("Building the demo's models (first run only)...", flush=True)
        coco = check_det_dataset("coco128.yaml")
        calibration = sorted(Path(coco["train"]).glob("*.jpg"))[:32]
        base_pt, small_pt = f"yolo11{args.base}.pt", f"yolo11{args.small}.pt"
        base_fp32 = YOLO(base_pt).export(format="onnx", imgsz=640, verbose=False)
        small_fp32 = YOLO(small_pt).export(format="onnx", imgsz=640, verbose=False)
        base_int8 = f"yolo11{args.base}_int8.onnx"
        print("Quantising to int8 (a minute or two)...", flush=True)
        quantize_int8(base_fp32, base_int8, calibration)
        device, device_name = gpu_device()

        name = f"YOLO11{args.base}"
        versions = [
            {"key": 1, "short": "float32", "label": f"{name}, float32", "engine": "ONNX Runtime, CPU",
             "file": base_fp32},
            {"key": 2, "short": "int8", "label": f"{name}, int8 (head float32)", "engine": "ONNX Runtime, CPU",
             "file": base_int8},
            {"key": 3, "short": f"YOLO11{args.small}", "label": f"YOLO11{args.small}, float32",
             "engine": "ONNX Runtime, CPU", "file": small_fp32},
            {"key": 4, "short": "GPU fp16", "label": f"{name}, float16", "engine": device_name or "no GPU on this laptop",
             "file": base_pt, "device": device, "half": True, "available": device is not None},
        ]
        for v in versions:
            v.setdefault("device", "cpu")
            v.setdefault("half", False)
            v.setdefault("available", True)
            v["file"] = str(CACHE / v["file"])
            v["MB"] = os.path.getsize(v["file"]) / 1e6 if not v["file"].endswith(".pt") else None
            v["mAP"] = None
            if v["available"] and not args.skip_map:
                print(f"Measuring accuracy on COCO128: {v['label']}...", flush=True)
                model = YOLO(v["file"], task="detect")
                v["mAP"] = model.val(data="coco128.yaml", imgsz=640, batch=1, device=v["device"], half=v["half"],
                                     plots=False, verbose=False).box.map
        summary_path.write_text(json.dumps({"base": args.base, "small": args.small, "versions": versions}, indent=2))
    finally:
        os.chdir(here)
    return versions


def print_table(versions):
    print(f"\n{'key':4s}{'version':30s}{'engine':22s}{'file MB':>9s}{'mAP50-95':>10s}")
    for v in versions:
        mb = f"{v['MB']:.1f}" if v["MB"] else "-"
        m = f"{v['mAP']:.3f}" if v["mAP"] is not None else "-"
        print(f"{v['key']:<4d}{v['label']:30s}{v['engine']:22s}{mb:>9s}{m:>10s}")
    print()


def load(versions):
    from ultralytics import YOLO
    for v in versions:
        v["model"] = YOLO(v["file"], task="detect") if v["available"] else None


def detect(v, frame):
    return v["model"].predict(frame, imgsz=640, device=v["device"], half=v["half"], verbose=False)[0]


def open_source(args):
    cap = cv2.VideoCapture(args.source if args.source else args.camera)
    if not args.source:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    ok, frame = cap.read() if cap.isOpened() else (False, None)
    if not ok:
        what = f"the video {args.source}" if args.source else f"camera {args.camera}"
        sys.exit(f"Could not read from {what}.\n"
                 "  - Another camera? Try --camera 1 (or 2).\n"
                 "  - macOS: System Settings > Privacy & Security > Camera: allow your terminal app "
                 "(Terminal, iTerm or VS Code), then restart it.\n"
                 "  - Windows: Settings > Privacy & security > Camera: let desktop apps use the camera.\n"
                 "  - No camera at all? Use --source with a video file.")
    return cap, frame


def next_frame(cap, args):
    ok, frame = cap.read()
    if not ok and args.source:                      # loop a video file
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        ok, frame = cap.read()
    return frame if ok else None


def draw_overlay(image, v, model_ms, fps, versions):
    h, w = image.shape[:2]
    scale = max(0.5, w / 1600)
    font, thick = cv2.FONT_HERSHEY_SIMPLEX, max(1, round(2 * scale))
    mb = f"{v['MB']:.1f} MB" if v["MB"] else "PyTorch weights"
    m = f"mAP50-95 {v['mAP']:.3f}" if v["mAP"] is not None else "mAP not measured"
    lines = [f"[{v['key']}] {v['label']}", f"{v['engine']} | {mb} | {m}",
             f"model {model_ms:.0f} ms per frame | {fps:.1f} FPS overall"]
    line_h = int(38 * scale)
    box_w = int(max(cv2.getTextSize(t, font, 0.9 * scale, thick)[0][0] for t in lines) + 30 * scale)
    overlay = image.copy()
    cv2.rectangle(overlay, (0, 0), (box_w, line_h * len(lines) + int(20 * scale)), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.6, image, 0.4, 0, image)
    for i, text in enumerate(lines):
        cv2.putText(image, text, (int(15 * scale), int((i + 1) * line_h)), font, 0.9 * scale,
                    (255, 255, 255), thick, cv2.LINE_AA)
    keys = "   ".join(f"{u['key']} {u['short']}" + ("" if u["available"] else " (n/a)") for u in versions)
    keys += "   q quit"
    cv2.putText(image, keys, (int(15 * scale), h - int(18 * scale)), font, 0.7 * scale, (0, 0, 0),
                thick + 3, cv2.LINE_AA)
    cv2.putText(image, keys, (int(15 * scale), h - int(18 * scale)), font, 0.7 * scale, (255, 255, 255),
                thick, cv2.LINE_AA)
    return image


def benchmark(versions, cap, args):
    print(f"{'version':30s}{'model ms':>10s}{'loop ms':>10s}{'FPS':>8s}")
    for v in versions:
        if not v["available"]:
            continue
        times, model_ms = [], []
        for i in range(args.benchmark + 5):
            frame = next_frame(cap, args)
            start = time.perf_counter()
            result = detect(v, frame)
            result.plot()
            if i >= 5:                                  # skip the warm-up frames
                times.append((time.perf_counter() - start) * 1000)
                model_ms.append(result.speed["inference"])
        loop = float(np.median(times))
        print(f"{v['label']:30s}{np.median(model_ms):10.1f}{loop:10.1f}{1000 / loop:8.1f}")


def snapshot(versions, frame, out_dir):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    for v in versions:
        if v["available"]:
            for _ in range(3):
                result = detect(v, frame)
            path = out / f"version_{v['key']}.png"
            cv2.imwrite(str(path), draw_overlay(result.plot(), v, result.speed["inference"], 0.0, versions))
            print("wrote", path)


def live(versions, cap, args):
    cv2.namedWindow(WINDOW, cv2.WINDOW_NORMAL)
    current, fps, last = 0, None, time.perf_counter()
    print("Keys: 1-4 switch version, q or Esc quits.")
    while True:
        frame = next_frame(cap, args)
        if frame is None:
            break
        v = versions[current]
        result = detect(v, frame)
        now = time.perf_counter()
        fps = 1 / (now - last) if fps is None else 0.9 * fps + 0.1 / (now - last)
        last = now
        cv2.imshow(WINDOW, draw_overlay(result.plot(), v, result.speed["inference"], fps, versions))
        key = cv2.waitKey(1) & 0xFF
        if key in (ord("q"), 27):
            break
        if ord("1") <= key < ord("1") + len(versions) and versions[key - ord("1")]["available"]:
            current, fps = key - ord("1"), None
    cap.release()
    cv2.destroyAllWindows()


def main():
    args = parse_args()
    versions = build(args)
    print_table(versions)
    load(versions)
    cap, frame = open_source(args)
    for v in versions:                                   # warm up, so switching is instant
        if v["available"]:
            detect(v, frame)
    if args.snapshot:
        snapshot(versions, frame, args.snapshot)
    elif args.benchmark:
        benchmark(versions, cap, args)
    else:
        live(versions, cap, args)


if __name__ == "__main__":
    main()
