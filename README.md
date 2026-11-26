# Smart File Organizer

Android पर Termux में चलने वाला यह Python ऐप चुने हुए source folder की सीधे अंदर वाली files को extension के आधार पर destination में रखता है। यह subfolders के अंदर नहीं जाता। Images, Documents, PDFs, Videos, Audio, Archives और Other files के लिए अलग folders बनते हैं। Python standard library का ही उपयोग होता है।

## Termux में स्थापना

1. Termux खोलकर Python और shared-storage access तैयार करें:

   ```sh
   pkg update
   pkg install python
   termux-setup-storage
   ```

2. Android के permission संदेश पर Termux को files access की अनुमति दें। साझा storage आम तौर पर `/storage/emulated/0` या `~/storage/shared` पर मिलता है।
3. इस project folder में जाएँ और ऐप चलाएँ:

   ```sh
   cd /data/data/com.termux/files/home/SmartFileOrganizer
   python main.py
   ```

`requirements.txt` में कोई अतिरिक्त package नहीं है; `pip install` की जरूरत नहीं।

## उपयोग

1. Menu में `1` दबाकर source और destination के पूरे paths दें। उदाहरण: source `~/storage/shared/Download`, destination `~/storage/shared/Organized`।
2. `2` दबाकर preview देखें। यह default सुरक्षित mode है और कोई file move नहीं करता।
3. Files move करने के लिए `3` दबाएँ। ऐप पहले पूरी सूची और नए paths दिखाएगा। फिर `yes` लिखकर ही आगे बढ़ेगा।
4. पिछला organization वापस करने के लिए `4` चुनें और वही destination folder दें। Undo की जानकारी destination में रखी जाती है।
5. TXT report destination folder में बनेगी।

अगर उसी नाम की file पहले से हो तो ऐप `name (1).ext`, फिर `name (2).ext` जैसे अलग नाम चुनता है। मौजूदा file overwrite नहीं होती। हर operation में केवल चुने हुए folders इस्तेमाल होते हैं; source और destination एक-दूसरे के अंदर नहीं हो सकते। Symbolic links और subfolders छोड़ दिए जाते हैं। Permission error आए तो Android Settings में Termux की file permission देखें और `termux-setup-storage` फिर चलाएँ। Root access की जरूरत नहीं है।

## Tests

Tests temporary folders बनाते हैं और फोन की personal files को नहीं छूते:

```sh
python -m unittest -v
```
