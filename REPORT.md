# Sistem za zaznavanje utrujenosti voznikov iz slik in videa

## 1. Uvod
Utrujenost voznika je pomemben dejavnik prometnih nesreč, zato je avtomatsko zaznavanje znakov zaspanosti ključnega pomena. Predlagana rešitev temelji na dveh opaznih signalih:
1. **zapiranje oči** (PERCLOS),
2. **nagib glave** (roll kot).

Rešitev je implementirana brez uporabe samostojne vnaprej naučene drowsiness rešitve. Uporabljeni so klasični računalniški vidni postopki in lastno učenje klasifikatorja za stanje oči.

## 2. Podatkovne zbirke

### 2.1 NTHU Drowsy Driver Detection Dataset
Priporočena zbirka za končno evalvacijo drowsy/alert na video sekvencah. Omogoča:
- scenarije z/brez očal,
- različne svetlobne pogoje,
- anotacije zaspanosti.

### 2.2 Dodatne zbirke
Za učenje modula za oči priporočamo:
- **CEW (Closed Eyes in the Wild)** ali ekvivalent,
- poljubno zbirko z razredi `open` in `closed`.

V implementaciji je predvidena mapa:
- `DATASET/open/*.jpg`
- `DATASET/closed/*.jpg`

## 3. Metoda

### 3.1 Zaznava obraza in oči
- Obraz: Viola–Jones (OpenCV Haar cascade).
- Oči: Haar detector za oči z očali.

### 3.2 Klasifikacija stanja oči
Za vsak zaznan očesni izrez:
- normalizacija na 24x24,
- HOG opisnik,
- linearni SVM, naučen iz podatkov (`open`, `closed`).

S tem dobimo verjetnost `p_closed`. Iz časovnega okna se izračuna **PERCLOS**.

### 3.3 Ocena nagiba glave
Na ROI obraza izračunamo centralne momente binarizirane slike in iz njih orientacijo elipse:
\[
\theta = \frac{1}{2}\arctan\left(\frac{2\mu_{11}}{\mu_{20}-\mu_{02}}\right)
\]

`|theta|` predstavlja nagib glave (roll).

**Pomembno:** metoda ocenjuje predvsem **roll nagib** (levo/desno) in je približna 2D ocena. Za zanesljivo zaznavo nagiba naprej/nazaj (pitch) bi bila potrebna analiza obraznih točk ali 3D head-pose ocena.

### 3.4 Končna odločitev
Drowsiness score:
\[
s = 0.65 \cdot \mathrm{PERCLOS} + 0.35 \cdot \min(|\theta|/35, 1)
\]

Stanje = `DROWSY`, če je `s > 0.5` ali `|theta| > tilt_thr`.

## 4. Implementacija
Glavna skripta: `drowsiness.py`

### Pod-ukazi
1. Učenje modela oči:
```bash
python drowsiness.py train-eye --dataset DATASET --out eye_svm.yml
```

2. Obdelava videa + izvoz napovedi v CSV:
```bash
python drowsiness.py run-video --input input.mp4 --output output.mp4 --eye-model eye_svm.yml --pred-csv results/preds.csv --y-true 0
```

3. Evalvacija metrik + ROC/AUC:
```bash
python drowsiness.py evaluate --pred-csv results/preds.csv --out-roc roc.png
```

`run-video` zapiše CSV s stolpci:
- `frame`
- `y_true`
- `y_pred`
- `score`
- `perclos`
- `roll`

## 5. Označevanje podatkov (`y_true`)
Za šolsko nalogo je preprost in korekten pristop:
- `video_alert_01.mp4` → `y_true = 0`
- `video_drowsy_01.mp4` → `y_true = 1`

Pri obdelavi posameznega videa podamo `--y-true`, skripta pa to oznako pripiše vsem frame-om tega videa.

## 6. Evalvacija
Uporabljene metrike:
- Accuracy
- Precision
- Recall
- F1
- ROC krivulja
- AUC

Skripta `evaluate` izračuna vse metrike in shrani ROC graf (`roc.png`).

## 7. Časovna in prostorska zahtevnost
Naj bo:
- `F` število okvirjev,
- `R` število pikslov ROI,
- `E` število zaznanih oči (običajno <=2),
- `d` dimenzija HOG značilk.

### Časovna
Na okvir približno:
- zaznava obraza/oči: odvisna od kaskad, dominantni del,
- HOG + SVM: `O(E * d)`,
- momenti ROI: `O(R)`.

Skupno za video: približno linearno v številu okvirjev `O(F * (cascade + R + E*d))`.

### Prostorska
- frame buffer + ROI: `O(R)`,
- zgodovina PERCLOS okna `W`: `O(W)`,
- model SVM: `O(d)` uteži,
- tabela napovedi: `O(F)` vrstic, če hranimo vse v pomnilniku do zapisa na disk.

Skupna poraba pomnilnika je nizka in primerna za izvajanje blizu realnega časa.

## 8. Možne izboljšave
- robustnejša zaznava v nočnih pogojih (IR, histogram equalization),
- adaptivni pragovi po uporabniku,
- dodatni kazalniki (zehanje, trajanje zaprtja oči),
- temporalni modeli (npr. HMM/LSTM, naučeni iz podatkov).
