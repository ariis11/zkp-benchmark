# Image Conversion and Proof Generation Commands

This file contains all the commands needed to convert images to JSON and generate proofs for each transformation type.

## Usage Instructions

1. **Navigate to the image_converter directory:**
   ```bash
   cd image_converter
   ```

2. **Step 1:** Convert images to JSON using `batch_convert.sh`
3. **Step 2:** Generate proofs using `batch_generate_proofs.sh`

---

## Resize Transformation

### Convert Images to JSON
```bash
./batch_convert.sh resize passports_hd resize/outputs_hd
```

### Generate Proofs
```bash
./batch_generate_proofs.sh image_converter/resize/outputs_hd image_converter/resize/proofs resize HD
```

---

## Contrast Transformation

### Convert Images to JSON
```bash
# Default contrast factor (1.5)
./batch_convert.sh contrast passports_hd contrast/outputs_hd

# Custom contrast factor (e.g., 1.4)
./batch_convert.sh contrast passports_hd contrast/outputs_hd 1.4
```

### Generate Proofs
```bash
./batch_generate_proofs.sh image_converter/contrast/outputs_hd image_converter/contrast/proofs contrast HD
```

---

## Crop Transformation

### Convert Images to JSON
```bash
# Default crop coordinates (x=0, y=0)
./batch_convert.sh crop passports_hd crop/outputs_hd

# Custom crop coordinates (requires script modification or direct python call)
cd crop
python3 crop.py -i ../passports_hd/passport_0000.png -o outputs_hd/passport_0000.json -r HD --crop-x 100 --crop-y 50
```

### Generate Proofs
```bash
./batch_generate_proofs.sh image_converter/crop/outputs_hd image_converter/crop/proofs crop HD
```

---

## Grayscale Transformation

### Convert Images to JSON
```bash
./batch_convert.sh grayscale passports_hd grayscale/outputs_hd
```

### Generate Proofs
```bash
./batch_generate_proofs.sh image_converter/grayscale/outputs_hd image_converter/grayscale/proofs grayscale HD
```

---

## Brightness Transformation

### Convert Images to JSON
```bash
# Default brightness factor (1.5)
./batch_convert.sh brightness passports_hd brightness/outputs_hd

# Custom brightness factor (e.g., 1.4)
./batch_convert.sh brightness passports_hd brightness/outputs_hd 1.4
```

### Generate Proofs
```bash
./batch_generate_proofs.sh image_converter/brightness/outputs_hd image_converter/brightness/proofs brightness HD
```

---

## Sharpness Transformation

### Convert Images to JSON
```bash
./batch_convert.sh sharpness passports_hd sharpness/outputs_hd
```

### Generate Proofs
```bash
./batch_generate_proofs.sh image_converter/sharpness/outputs_hd image_converter/sharpness/proofs sharpness HD
```

---

## Blur Transformation

### Convert Images to JSON
```bash
./batch_convert.sh blur passports_hd blur/outputs_hd
```

### Generate Proofs
```bash
./batch_generate_proofs.sh image_converter/blur/outputs_hd image_converter/blur/proofs blur HD
```

---

## Notes

- All commands should be run from the `image_converter/` directory
- Input images are expected in `passports_hd/` directory
- JSON files are saved to `<transformation>/outputs_hd/`
- Proofs and logs are saved to `<transformation>/proofs/`
- Performance results are saved to `<transformation>/performance_results.json`
- For transformations with factors (contrast, brightness), the default is 1.5
- Crop transformation uses optimized_crop circuit automatically
- All other transformations use standard `<transformation>_step_HD` circuits

---
