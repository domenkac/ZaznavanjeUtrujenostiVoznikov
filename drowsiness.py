import argparse
import json
import os
from collections import deque

import cv2
import numpy as np
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_curve, auc


class EyeStateClassifier:
    """Simple CNN-like fallback using HOG+Linear SVM trained from scratch on labeled eye images."""

    def __init__(self):
        self.model = cv2.ml.SVM_create()
        self.model.setType(cv2.ml.SVM_C_SVC)
        self.model.setKernel(cv2.ml.SVM_LINEAR)
        self.model.setC(1.0)
        self.hog = cv2.HOGDescriptor((24, 24), (12, 12), (6, 6), (6, 6), 9)

    def _features(self, img):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
        gray = cv2.resize(gray, (24, 24))
        return self.hog.compute(gray).flatten()

    def fit(self, images, labels):
        X = np.array([self._features(im) for im in images], dtype=np.float32)
        y = np.array(labels, dtype=np.int32)
        self.model.train(X, cv2.ml.ROW_SAMPLE, y)

    def predict_proba(self, img):
        x = self._features(img).astype(np.float32)[None, :]
        _, raw = self.model.predict(x, flags=cv2.ml.StatModel_RAW_OUTPUT)
        # Convert margin to probability-like value with sigmoid
        margin = -raw[0, 0]
        p_closed = 1.0 / (1.0 + np.exp(-margin))
        return float(np.clip(p_closed, 0.0, 1.0))


class HeadTiltEstimator:
    """Face roll estimator based on image moments on the face ROI."""

    @staticmethod
    def estimate_roll_deg(face_roi):
        gray = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        _, bw = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        m = cv2.moments(bw)
        if abs(m["mu20"] - m["mu02"]) < 1e-6:
            return 0.0
        theta = 0.5 * np.arctan2(2.0 * m["mu11"], (m["mu20"] - m["mu02"]))
        return float(np.degrees(theta))


class DrowsinessDetector:
    def __init__(self, eye_model_path=None, perclos_window=90, close_thr=0.6, tilt_thr=18.0):
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        self.eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_eye_tree_eyeglasses.xml")
        self.eye_classifier = EyeStateClassifier()
        if eye_model_path and os.path.exists(eye_model_path):
            self.eye_classifier.model = cv2.ml.SVM_load(eye_model_path)
        self.tilt_estimator = HeadTiltEstimator()
        self.close_hist = deque(maxlen=perclos_window)
        self.close_thr = close_thr
        self.tilt_thr = tilt_thr

    def detect(self, frame):
        out = frame.copy()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5, minSize=(90, 90))

        best = None
        if len(faces) > 0:
            best = max(faces, key=lambda b: b[2] * b[3])
            x, y, w, h = best
            cv2.rectangle(out, (x, y), (x + w, y + h), (80, 220, 80), 2)
            face_roi = frame[y:y + h, x:x + w]

            roll = self.tilt_estimator.estimate_roll_deg(face_roi)
            eyes = self.eye_cascade.detectMultiScale(gray[y:y + h, x:x + w], scaleFactor=1.1, minNeighbors=4)

            probs = []
            for (ex, ey, ew, eh) in eyes[:2]:
                patch = frame[y + ey:y + ey + eh, x + ex:x + ex + ew]
                if patch.size == 0:
                    continue
                p_closed = self.eye_classifier.predict_proba(patch)
                probs.append(p_closed)
                color = (0, 0, 255) if p_closed > self.close_thr else (255, 255, 0)
                cv2.rectangle(out, (x + ex, y + ey), (x + ex + ew, y + ey + eh), color, 2)

            p_closed_frame = float(np.mean(probs)) if probs else 0.0
            self.close_hist.append(1 if p_closed_frame > self.close_thr else 0)
            perclos = float(np.mean(self.close_hist)) if self.close_hist else 0.0

            drowsy_score = 0.65 * perclos + 0.35 * min(abs(roll) / 35.0, 1.0)
            is_drowsy = drowsy_score > 0.5 or abs(roll) > self.tilt_thr

            txt = f"PERCLOS={perclos:.2f} roll={roll:.1f} score={drowsy_score:.2f}"
            cv2.putText(out, txt, (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(out, "DROWSY" if is_drowsy else "ALERT", (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.9,
                        (0, 0, 255) if is_drowsy else (0, 255, 0), 2)

            return out, {
                "perclos": perclos,
                "roll": roll,
                "drowsy_score": drowsy_score,
                "pred": int(is_drowsy),
            }

        return out, {"perclos": 0.0, "roll": 0.0, "drowsy_score": 0.0, "pred": 0}


def load_eye_dataset(dataset_dir):
    images, labels = [], []
    for label_name, label in [("open", 0), ("closed", 1)]:
        d = os.path.join(dataset_dir, label_name)
        if not os.path.isdir(d):
            continue
        for fn in os.listdir(d):
            p = os.path.join(d, fn)
            img = cv2.imread(p)
            if img is None:
                continue
            images.append(img)
            labels.append(label)
    return images, labels


def train_eye_model(dataset_dir, out_path):
    imgs, y = load_eye_dataset(dataset_dir)
    if len(imgs) < 20:
        raise RuntimeError("Premalo podatkov. Pričakovane mape: dataset_dir/open in dataset_dir/closed")
    clf = EyeStateClassifier()
    clf.fit(imgs, y)
    clf.model.save(out_path)


def evaluate_csv(pred_csv, out_roc):
    import pandas as pd
    df = pd.read_csv(pred_csv)
    y_true = df["y_true"].values
    y_pred = df["y_pred"].values
    y_score = df["score"].values

    metrics = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
    }
    fpr, tpr, _ = roc_curve(y_true, y_score)
    metrics["auc"] = float(auc(fpr, tpr))

    canvas = np.ones((500, 500, 3), dtype=np.uint8) * 255
    pts = np.vstack([fpr, tpr]).T
    for i in range(1, len(pts)):
        x1, y1 = int(pts[i - 1, 0] * 450 + 30), int((1 - pts[i - 1, 1]) * 450 + 20)
        x2, y2 = int(pts[i, 0] * 450 + 30), int((1 - pts[i, 1]) * 450 + 20)
        cv2.line(canvas, (x1, y1), (x2, y2), (0, 0, 255), 2)
    cv2.line(canvas, (30, 470), (480, 20), (150, 150, 150), 1)
    cv2.putText(canvas, f"AUC={metrics['auc']:.3f}", (30, 490), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
    cv2.imwrite(out_roc, canvas)
    print(json.dumps(metrics, indent=2))


def run_video(video_in, video_out, eye_model):
    det = DrowsinessDetector(eye_model)
    cap = cv2.VideoCapture(video_in)
    if not cap.isOpened():
        raise RuntimeError(f"Ne morem odpreti videa: {video_in}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    writer = cv2.VideoWriter(video_out, cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        out, _ = det.detect(frame)
        writer.write(out)

    cap.release()
    writer.release()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    tr = sub.add_parser("train-eye")
    tr.add_argument("--dataset", required=True)
    tr.add_argument("--out", default="eye_svm.yml")

    rv = sub.add_parser("run-video")
    rv.add_argument("--input", required=True)
    rv.add_argument("--output", default="output.mp4")
    rv.add_argument("--eye-model", default="eye_svm.yml")

    ev = sub.add_parser("evaluate")
    ev.add_argument("--pred-csv", required=True)
    ev.add_argument("--out-roc", default="roc.png")

    args = ap.parse_args()
    if args.cmd == "train-eye":
        train_eye_model(args.dataset, args.out)
    elif args.cmd == "run-video":
        run_video(args.input, args.output, args.eye_model)
    elif args.cmd == "evaluate":
        evaluate_csv(args.pred_csv, args.out_roc)
