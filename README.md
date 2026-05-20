# Zaznavanje utrujenosti voznikov

Projekt implementira zaznavanje utrujenosti iz videa z uporabo:
- zapiranja oči (PERCLOS),
- nagiba glave.

Podrobno poročilo je v `REPORT.md`.

## Namestitev
```bash
pip install -r requirements.txt
```

## Hiter zagon
```bash
# 1) učenje modela oči
python drowsiness.py train-eye --dataset DATASET --out eye_svm.yml

# 2) zaznava na videu
python drowsiness.py run-video --input input.mp4 --output output.mp4 --eye-model eye_svm.yml

# 3) evalvacija
python drowsiness.py evaluate --pred-csv preds.csv --out-roc roc.png
```
