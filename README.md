# Zaznavanje utrujenosti voznikov

Projekt implementira zaznavanje utrujenosti iz videa z uporabo:
- zapiranja oči (PERCLOS),
- nagiba glave (približni roll levo/desno, izračunan iz položaja dveh zaznanih oči).

Podrobno poročilo je v `REPORT.md`.

## Namestitev
```bash
pip install -r requirements.txt
```

## Struktura podatkov

### 1) Učenje klasifikatorja oči
Pričakovana struktura:
```text
DATASET/
  open/
    img1.jpg
    ...
  closed/
    img1.jpg
    ...
```

### 2) Oznake videov (primer)
- `video_alert_01.mp4` → `y_true=0`
- `video_drowsy_01.mp4` → `y_true=1`

Za vsak video lahko pri `run-video` podaš enotno oznako `--y-true`, ki se zapiše za vse frame-e.

## Uporaba

```bash
# 1) učenje modela oči
python drowsiness.py train-eye --dataset DATASET --out eye_svm.yml

# 2) zaznava na videu + shranjevanje napovedi v CSV
python drowsiness.py run-video \
  --input video_alert_01.mp4 \
  --output results/alert_out.mp4 \
  --eye-model eye_svm.yml \
  --pred-csv results/alert_preds.csv \
  --y-true 0

python drowsiness.py run-video \
  --input video_drowsy_01.mp4 \
  --output results/drowsy_out.mp4 \
  --eye-model eye_svm.yml \
  --pred-csv results/drowsy_preds.csv \
  --y-true 1
```

`output.mp4` vsebuje anotiran video (obraz/oči, PERCLOS, roll, ALERT/DROWSY).

## Struktura `preds.csv`
`run-video` shrani stolpce:
- `frame`
- `y_true`
- `y_pred`
- `score`
- `perclos`
- `roll`
- `roll_valid` (`1`, če sta bili zaznani dve očesi in je roll veljaven; sicer `0`)

Primer:
```csv
frame,y_true,y_pred,score,perclos,roll,roll_valid
0,0,0,0.12,0.05,3.4,1
1,0,0,0.10,0.04,2.7,1
2,0,0,0.08,0.00,0.0,0
```

## Evalvacija
Če imaš en CSV z vsemi vzorci:
```bash
python drowsiness.py evaluate --pred-csv results/preds.csv --out-roc results/roc.png
```

Če imaš več CSV (npr. alert + drowsy), jih združiš npr. s pandas ali shell orodji in nato poženeš `evaluate`.


## Razlaga ocene nagiba glave
Roll se izračuna iz naklona premice med središčema dveh zaznanih oči. Če program ne zazna dveh uporabnih oči, nastavi `roll_valid=0`, roll pa ne vpliva na končno odločitev. S tem se preprečijo lažni alarmi zaradi nerealnih kotov, ki jih je prejšnja metoda z momenti celotnega obraza lahko ocenila blizu ±90°. Po posodobitvi kode modela oči ni treba ponovno učiti; ponovno je treba pognati le `run-video`, da nastaneta nov video in CSV.
