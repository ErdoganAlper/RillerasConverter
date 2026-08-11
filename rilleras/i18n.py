"""Translations.

Pure Python with no UI or engine imports, so both `core` and `app` can use it.
Look-ups fall back to English when a key is missing from a language, and to the
key itself when it is missing everywhere — a missing string shows up as an
obvious `like.this` marker rather than a crash.

Adding a language: add a code to LANGUAGES and a table to TRANSLATIONS. The
test suite asserts every language defines exactly the English key set.
"""

from __future__ import annotations

LANGUAGES = {
    "en": "English",
    "tr": "Türkçe",
}

DEFAULT_LANGUAGE = "en"
_current = DEFAULT_LANGUAGE


def set_language(code: str) -> str:
    global _current
    _current = code if code in LANGUAGES else DEFAULT_LANGUAGE
    return _current


def get_language() -> str:
    return _current


def t(key: str, **kwargs) -> str:
    """Translate ``key`` into the active language."""
    table = TRANSLATIONS.get(_current, {})
    text = table.get(key)
    if text is None:
        text = TRANSLATIONS[DEFAULT_LANGUAGE].get(key, key)
    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, IndexError):
            pass  # never let a bad placeholder break the UI
    return text


EN: dict[str, str] = {
    # ---- navigation & chrome
    "nav.main": "Convert",
    "nav.pdf": "PDF Tools",
    "nav.image": "Image Tools",
    "nav.batch": "Batch Word",
    "nav.settings": "Settings",
    "nav.log": "Activity Log",
    "header.preset": "Quality preset",
    "sidebar.drop_hint": "Drop a file anywhere\nto load it",
    "sidebar.dnd_off": "Drag & drop disabled",
    "panel.choose": "Choose a conversion",

    # ---- groups
    "group.main.title": "Convert",
    "group.main.sub": "Everyday document and image conversions",
    "group.pdf.title": "PDF Tools",
    "group.pdf.sub": "Merge, split, rotate and shrink PDF files",
    "group.image.title": "Image Tools",
    "group.image.sub": "Bulk operations across a folder of images",
    "group.batch.title": "Batch Word",
    "group.batch.sub": "Process a whole folder of Word documents",

    # ---- modes
    "mode.pdf_to_word.title": "PDF → Word",
    "mode.pdf_to_word.sub": "Editable .docx with layout kept",
    "mode.word_to_pdf.title": "Word → PDF",
    "mode.word_to_pdf.sub": "Needs Microsoft Word installed",
    "mode.pdf_to_images.title": "PDF → Images",
    "mode.pdf_to_images.sub": "One image file per page",
    "mode.images_to_pdf.title": "Images → PDF",
    "mode.images_to_pdf.sub": "Lossless, naturally sorted",
    "mode.images_to_word.title": "Images → Word",
    "mode.images_to_word.sub": "One picture per page in a .docx",
    "mode.word_to_images.title": "Word → Images",
    "mode.word_to_images.sub": "Via Word, then rendered per page",
    "mode.pdf_to_text.title": "PDF → Text",
    "mode.pdf_to_text.sub": "Plain .txt from the text layer",
    "mode.pdf_to_long_image.title": "PDF → Long Image",
    "mode.pdf_to_long_image.sub": "All pages stitched vertically",
    "mode.pdf_to_images_only_img_pages.title": "PDF → Images (image pages)",
    "mode.pdf_to_images_only_img_pages.sub": "Skips pages with no pictures",
    "mode.image_to_image.title": "Image → Image",
    "mode.image_to_image.sub": "Convert format, optionally resize",
    "mode.merge_pdfs.title": "Merge PDFs",
    "mode.merge_pdfs.sub": "Combine many files into one",
    "mode.split_pdf.title": "Split PDF",
    "mode.split_pdf.sub": "Every page, or custom ranges",
    "mode.rotate_pdf.title": "Rotate PDF",
    "mode.rotate_pdf.sub": "Turn selected pages 90/180/270°",
    "mode.compress_pdf.title": "Compress PDF",
    "mode.compress_pdf.sub": "Clean up, or rebuild at lower DPI",
    "mode.batch_image_convert.title": "Batch Convert Images",
    "mode.batch_image_convert.sub": "Whole folder to one format",
    "mode.batch_image_resize.title": "Batch Resize Images",
    "mode.batch_image_resize.sub": "Shrink to a max dimension",
    "mode.images_to_pdf_per_subfolder.title": "Subfolders → PDFs",
    "mode.images_to_pdf_per_subfolder.sub": "One PDF per subfolder",
    "mode.batch_word_pdf.title": "Word folder → PDFs",
    "mode.batch_word_pdf.sub": "Every .docx in a folder",
    "mode.batch_word_images.title": "Word folder → Images",
    "mode.batch_word_images.sub": "A subfolder of images per .docx",

    # ---- input / output descriptions
    "io.in.docx": "Input Word document (.docx)",
    "io.in.pdf": "Input PDF (.pdf)",
    "io.in.folder": "Input folder",
    "io.in.image_or_folder": "Input image or folder",
    "io.in.none": "Not used — build the merge list below",
    "io.out.folder": "Output folder",
    "io.out.pdf": "Output PDF (.pdf)",
    "io.out.docx": "Output Word document (.docx)",
    "io.out.txt": "Output text file (.txt)",
    "io.out.image": "Output image (.png / .jpg)",
    "io.out.image_or_folder": "Output folder, or a file when the input is one image",

    # ---- cards & fields
    "card.files.title": "Files",
    "card.files.sub": "where to read from and write to",
    "card.merge.title": "Merge list",
    "card.merge.sub": "files are merged top to bottom",
    "card.options.title": "Options",
    "card.options.sub": "only what applies to this conversion",
    "card.behaviour": "Behaviour",
    "card.language": "Language",
    "card.storage": "Storage",
    "card.about": "About",
    "card.log.title": "Activity log",
    "field.recent": "Recent",
    "field.input": "Input",
    "field.output": "Output",

    # ---- buttons
    "btn.clear": "Clear",
    "btn.browse": "Browse…",
    "btn.add_pdfs": "Add PDFs…",
    "btn.move_up": "Move up",
    "btn.move_down": "Move down",
    "btn.remove": "Remove",
    "btn.copy_all": "Copy all",
    "btn.open_settings_folder": "Open settings folder",
    "btn.open_output": "Open output",
    "btn.cancel": "Cancel",
    "btn.run": "Run conversion",

    # ---- options
    "opt.dpi": "DPI",
    "opt.format": "Format",
    "opt.jpg_quality": "JPG quality",
    "opt.pages": "Pages",
    "opt.pages_hint": "all,  or  1-3,7,10-",
    "opt.recursive": "Include images in subfolders",
    "opt.sort": "Page order",
    "opt.sort_hint": "natural puts page2 before page10",
    "opt.save_as": "Save as",
    "opt.max_size": "Max size (px)",
    "opt.quality": "Quality",
    "opt.rotate_by": "Rotate by",
    "opt.degrees_cw": "degrees clockwise",
    "opt.split": "Split",
    "opt.ranges": "Ranges",
    "opt.ranges_hint": "used when split = ranges",
    "opt.method": "Method",
    "opt.rebuild_dpi": "Rebuild DPI",
    "opt.compress_hint": "clean is lossless; rebuild re-renders pages",

    # ---- settings screen
    "settings.remember_paths": "Remember the last input and output paths between runs",
    "settings.open_after": "Open the output folder automatically when a job finishes",
    "settings.confirm_overwrite": "Ask before overwriting existing files",
    "settings.language_hint": "The interface updates as soon as you pick a language.",
    "settings.file_location": "Settings file: {path}",
    "about.version": "Rilleras Converter {version}",
    "about.dnd": "Drag & drop: {state}",
    "about.dnd_on": "enabled",
    "about.dnd_off": "not installed (pip install tkinterdnd2)",
    "about.word": "Word conversions drive Microsoft Word and need it installed.",
    "about.pdf2docx": "PDF → Word uses pdf2docx and keeps the page layout.",
    "badge.requires_word": "  ⚠  Requires Microsoft Word installed on this PC  ",

    # ---- status bar
    "status.ready": "Ready",
    "status.working": "Working…",
    "status.finished": "Finished",
    "status.cancelled": "Cancelled",
    "status.failed": "Failed",
    "status.check_settings": "Check settings",
    "status.see_log": "see Activity Log",
    "status.progress": "{done} of {total}",

    # ---- log lines
    "log.ready": "Rilleras Converter ready.",
    "log.dnd_missing": "Drag & drop unavailable (tkinterdnd2 not installed).",
    "log.starting": "Starting: {title}",
    "log.finished": "Finished → {path}",
    "log.cancelled": "Cancelled.",
    "log.cancel_requested": "Cancel requested…",
    "log.preset_applied": "Preset applied: {name}",
    "log.copied": "Log copied to clipboard.",
    "log.loaded": "Loaded: {path}",
    "log.language_changed": "Language: {name}",

    # ---- dialogs
    "dlg.merge_title": "Merge PDFs",
    "dlg.merge_use_list": "Use 'Add PDFs…' in the merge list below.",
    "dlg.select_pdfs_merge": "Select PDFs to merge",
    "dlg.select_word": "Select Word document",
    "dlg.select_pdf": "Select PDF",
    "dlg.select_folder": "Select folder",
    "dlg.select_images_folder": "Select folder of images",
    "dlg.select_image": "Select image",
    "dlg.choose_input": "Choose input",
    "dlg.folder_or_file": "Convert a whole folder?\n\nYes — pick a folder\nNo — pick a single image",
    "dlg.select_out_folder": "Select output folder",
    "dlg.save_pdf": "Save PDF as",
    "dlg.save_docx": "Save Word document as",
    "dlg.save_txt": "Save text file as",
    "dlg.save_image": "Save image as",
    "dlg.folder_not_empty": "Folder is not empty",
    "dlg.folder_not_empty_body": "{path}\n\nExisting files with the same names will be replaced. Continue?",
    "dlg.overwrite_file": "Overwrite file?",
    "dlg.overwrite_file_body": "{path}\n\nReplace this file?",
    "dlg.cannot_run": "Cannot run",
    "dlg.failed": "Conversion failed",
    "filetype.images": "Images",
    "filetype.pdf": "PDF",
    "filetype.word": "Word",
    "filetype.text": "Text",
    "filetype.image": "Image",

    # ---- engine errors
    "err.no_images": "No images found.",
    "err.input_required": "Choose an input path.",
    "err.output_required": "Choose an output path.",
    "err.input_missing": "Input path does not exist:\n{path}",
    "err.input_docx": "Input must be a .docx file.",
    "err.input_pdf": "Input must be a .pdf file.",
    "err.input_folder": "Input must be a folder.",
    "err.input_image": "Input must be an image file.",
    "err.output_folder_expected": ("This conversion writes many files, so the output must be a "
                                   "folder.\n'{name}' looks like a file."),
    "err.output_image_ext": "Output image must be .png or .jpg",
    "err.merge_empty": "The merge list is empty — add some PDFs first.",
    "err.dpi_range": "DPI must be between 72 and 600.",
    "err.format_png_jpg": "Format must be png or jpg.",
    "err.choose_out_format": "Choose an output format from: {formats}",
    "err.whole_number": "{field} must be a whole number (got '{value}').",
    "err.page_range": "Could not read page range '{part}'. Use formats like: all, 1-3,7,10-",
    "err.no_pages": "No pages selected.",
    "err.no_pages_or_images": "No pages selected (or no pages with images).",
    "err.unsupported_format": "Unsupported output format: {fmt}",
    "err.save_failed": ("Failed saving as .{fmt}. Your Pillow build may not support it.\n"
                        "Details: {details}"),
    "err.ranges_required": "Provide ranges like 1-3,4-7",
    "err.ranges_format": "Ranges must be like 1-3,4-7",
    "err.range_unreadable": "Could not read range '{block}'.",
    "err.no_pdfs": "No PDFs selected.",
    "err.no_docx_in_folder": "No .docx files found in folder.",
    "err.no_subfolders": "No subfolders found. Put images into subfolders.",
    "err.image_no_size": "Image has no size: {path}",
    "err.unknown_mode": "Unknown mode: {key}",
    "err.word_unavailable": ("Word → PDF is unavailable. {why}\n\n"
                             "This conversion automates Microsoft Word, so Word must be "
                             "installed and licensed on this PC."),
    "err.pdf2docx_missing": ("PDF → Word needs the 'pdf2docx' package.\n"
                             "Install it with:  pip install pdf2docx\nDetails: {details}"),
    "err.pythondocx_missing": ("Images → Word needs the 'python-docx' package.\n"
                               "Install it with:  pip install python-docx\nDetails: {details}"),
    "err.pdf_to_word_failed": "PDF → Word failed: {details}",
    "why.not_windows": "Word conversion needs Microsoft Word on Windows.",
    "why.no_docx2pdf": "The 'docx2pdf' package is not installed.",
    "why.no_word": "Microsoft Word does not appear to be installed.",
    "why.word_ok": "Microsoft Word detected.",

    # ---- engine progress messages
    "msg.saved": "Saved: {path}",
    "msg.created": "Created: {path}",
    "msg.added": "Added: {path}",
    "msg.found_images": "Found {count} images. Creating PDF...",
    "msg.word_to_pdf": "Word → PDF (driving Microsoft Word)...",
    "msg.created_clean": "Created (clean/deflate): {path}",
    "msg.created_rebuild": "Created (rebuild at {dpi} dpi): {path}",
    "msg.pdf_no_text_layer": ("Note: this PDF has no text layer (likely a scan). "
                              "Output will contain page images, not editable text."),
    "msg.converting_pages": "Converting {count} page(s) to Word — this can take a while...",
}

TR: dict[str, str] = {
    # ---- navigation & chrome
    "nav.main": "Dönüştür",
    "nav.pdf": "PDF Araçları",
    "nav.image": "Görsel Araçları",
    "nav.batch": "Toplu Word",
    "nav.settings": "Ayarlar",
    "nav.log": "İşlem Günlüğü",
    "header.preset": "Kalite ayarı",
    "sidebar.drop_hint": "Dosyayı pencereye\nsürükleyip bırakın",
    "sidebar.dnd_off": "Sürükle-bırak kapalı",
    "panel.choose": "Bir dönüştürme seçin",

    # ---- groups
    "group.main.title": "Dönüştür",
    "group.main.sub": "Günlük belge ve görsel dönüştürmeleri",
    "group.pdf.title": "PDF Araçları",
    "group.pdf.sub": "PDF dosyalarını birleştirin, bölün, döndürün ve küçültün",
    "group.image.title": "Görsel Araçları",
    "group.image.sub": "Bir klasördeki görsellerde toplu işlemler",
    "group.batch.title": "Toplu Word",
    "group.batch.sub": "Bir klasördeki tüm Word belgelerini işleyin",

    # ---- modes
    "mode.pdf_to_word.title": "PDF → Word",
    "mode.pdf_to_word.sub": "Düzeni korunmuş, düzenlenebilir .docx",
    "mode.word_to_pdf.title": "Word → PDF",
    "mode.word_to_pdf.sub": "Microsoft Word kurulu olmalı",
    "mode.pdf_to_images.title": "PDF → Görseller",
    "mode.pdf_to_images.sub": "Her sayfa için bir görsel dosyası",
    "mode.images_to_pdf.title": "Görseller → PDF",
    "mode.images_to_pdf.sub": "Kayıpsız, doğal sıralamayla",
    "mode.images_to_word.title": "Görseller → Word",
    "mode.images_to_word.sub": ".docx içinde her sayfada bir görsel",
    "mode.word_to_images.title": "Word → Görseller",
    "mode.word_to_images.sub": "Word ile açılır, sayfa sayfa işlenir",
    "mode.pdf_to_text.title": "PDF → Metin",
    "mode.pdf_to_text.sub": "Metin katmanından düz .txt",
    "mode.pdf_to_long_image.title": "PDF → Uzun Görsel",
    "mode.pdf_to_long_image.sub": "Tüm sayfalar alt alta birleştirilir",
    "mode.pdf_to_images_only_img_pages.title": "PDF → Görseller (resimli sayfalar)",
    "mode.pdf_to_images_only_img_pages.sub": "Resim içermeyen sayfaları atlar",
    "mode.image_to_image.title": "Görsel → Görsel",
    "mode.image_to_image.sub": "Biçim değiştir, istenirse boyutlandır",
    "mode.merge_pdfs.title": "PDF Birleştir",
    "mode.merge_pdfs.sub": "Birden çok dosyayı tek dosyada topla",
    "mode.split_pdf.title": "PDF Böl",
    "mode.split_pdf.sub": "Her sayfa veya özel aralıklar",
    "mode.rotate_pdf.title": "PDF Döndür",
    "mode.rotate_pdf.sub": "Seçili sayfaları 90/180/270° çevir",
    "mode.compress_pdf.title": "PDF Sıkıştır",
    "mode.compress_pdf.sub": "Temizle veya düşük DPI ile yeniden oluştur",
    "mode.batch_image_convert.title": "Toplu Görsel Dönüştür",
    "mode.batch_image_convert.sub": "Tüm klasörü tek biçime çevir",
    "mode.batch_image_resize.title": "Toplu Görsel Boyutlandır",
    "mode.batch_image_resize.sub": "En büyük kenara göre küçült",
    "mode.images_to_pdf_per_subfolder.title": "Alt Klasörler → PDF'ler",
    "mode.images_to_pdf_per_subfolder.sub": "Her alt klasör için bir PDF",
    "mode.batch_word_pdf.title": "Word klasörü → PDF'ler",
    "mode.batch_word_pdf.sub": "Klasördeki her .docx dosyası",
    "mode.batch_word_images.title": "Word klasörü → Görseller",
    "mode.batch_word_images.sub": "Her .docx için bir görsel klasörü",

    # ---- input / output descriptions
    "io.in.docx": "Girdi Word belgesi (.docx)",
    "io.in.pdf": "Girdi PDF dosyası (.pdf)",
    "io.in.folder": "Girdi klasörü",
    "io.in.image_or_folder": "Girdi görseli veya klasörü",
    "io.in.none": "Kullanılmıyor — aşağıdaki birleştirme listesini doldurun",
    "io.out.folder": "Çıktı klasörü",
    "io.out.pdf": "Çıktı PDF dosyası (.pdf)",
    "io.out.docx": "Çıktı Word belgesi (.docx)",
    "io.out.txt": "Çıktı metin dosyası (.txt)",
    "io.out.image": "Çıktı görseli (.png / .jpg)",
    "io.out.image_or_folder": "Çıktı klasörü, girdi tek görselse bir dosya",

    # ---- cards & fields
    "card.files.title": "Dosyalar",
    "card.files.sub": "nereden okunacak, nereye yazılacak",
    "card.merge.title": "Birleştirme listesi",
    "card.merge.sub": "dosyalar yukarıdan aşağıya birleştirilir",
    "card.options.title": "Seçenekler",
    "card.options.sub": "yalnızca bu dönüştürmeyi ilgilendirenler",
    "card.behaviour": "Davranış",
    "card.language": "Dil",
    "card.storage": "Depolama",
    "card.about": "Hakkında",
    "card.log.title": "İşlem günlüğü",
    "field.recent": "Son kullanılan",
    "field.input": "Girdi",
    "field.output": "Çıktı",

    # ---- buttons
    "btn.clear": "Temizle",
    "btn.browse": "Gözat…",
    "btn.add_pdfs": "PDF ekle…",
    "btn.move_up": "Yukarı taşı",
    "btn.move_down": "Aşağı taşı",
    "btn.remove": "Kaldır",
    "btn.copy_all": "Tümünü kopyala",
    "btn.open_settings_folder": "Ayarlar klasörünü aç",
    "btn.open_output": "Çıktıyı aç",
    "btn.cancel": "İptal",
    "btn.run": "Dönüştürmeyi başlat",

    # ---- options
    "opt.dpi": "DPI",
    "opt.format": "Biçim",
    "opt.jpg_quality": "JPG kalitesi",
    "opt.pages": "Sayfalar",
    "opt.pages_hint": "tümü,  ya da  1-3,7,10-",
    "opt.recursive": "Alt klasörlerdeki görselleri de al",
    "opt.sort": "Sayfa sırası",
    "opt.sort_hint": "doğal sıralama page2'yi page10'dan önce koyar",
    "opt.save_as": "Farklı kaydet",
    "opt.max_size": "En büyük kenar (px)",
    "opt.quality": "Kalite",
    "opt.rotate_by": "Döndürme",
    "opt.degrees_cw": "derece, saat yönünde",
    "opt.split": "Bölme",
    "opt.ranges": "Aralıklar",
    "opt.ranges_hint": "bölme = aralıklar seçiliyken kullanılır",
    "opt.method": "Yöntem",
    "opt.rebuild_dpi": "Yeniden oluşturma DPI",
    "opt.compress_hint": "temizle kayıpsızdır; yeniden oluştur sayfaları baştan işler",

    # ---- settings screen
    "settings.remember_paths": "Son kullanılan girdi ve çıktı yollarını hatırla",
    "settings.open_after": "İşlem bitince çıktı klasörünü kendiliğinden aç",
    "settings.confirm_overwrite": "Var olan dosyaların üzerine yazmadan önce sor",
    "settings.language_hint": "Dili seçtiğiniz anda arayüz güncellenir.",
    "settings.file_location": "Ayar dosyası: {path}",
    "about.version": "Rilleras Converter {version}",
    "about.dnd": "Sürükle-bırak: {state}",
    "about.dnd_on": "etkin",
    "about.dnd_off": "kurulu değil (pip install tkinterdnd2)",
    "about.word": "Word dönüştürmeleri Microsoft Word'ü kullanır, kurulu olması gerekir.",
    "about.pdf2docx": "PDF → Word, pdf2docx kullanır ve sayfa düzenini korur.",
    "badge.requires_word": "  ⚠  Bu bilgisayarda Microsoft Word kurulu olmalı  ",

    # ---- status bar
    "status.ready": "Hazır",
    "status.working": "Çalışıyor…",
    "status.finished": "Tamamlandı",
    "status.cancelled": "İptal edildi",
    "status.failed": "Başarısız",
    "status.check_settings": "Ayarları kontrol edin",
    "status.see_log": "işlem günlüğüne bakın",
    "status.progress": "{done} / {total}",

    # ---- log lines
    "log.ready": "Rilleras Converter hazır.",
    "log.dnd_missing": "Sürükle-bırak kullanılamıyor (tkinterdnd2 kurulu değil).",
    "log.starting": "Başlıyor: {title}",
    "log.finished": "Tamamlandı → {path}",
    "log.cancelled": "İptal edildi.",
    "log.cancel_requested": "İptal isteği gönderildi…",
    "log.preset_applied": "Ayar uygulandı: {name}",
    "log.copied": "Günlük panoya kopyalandı.",
    "log.loaded": "Yüklendi: {path}",
    "log.language_changed": "Dil: {name}",

    # ---- dialogs
    "dlg.merge_title": "PDF birleştir",
    "dlg.merge_use_list": "Aşağıdaki birleştirme listesinde 'PDF ekle…' düğmesini kullanın.",
    "dlg.select_pdfs_merge": "Birleştirilecek PDF'leri seçin",
    "dlg.select_word": "Word belgesi seçin",
    "dlg.select_pdf": "PDF seçin",
    "dlg.select_folder": "Klasör seçin",
    "dlg.select_images_folder": "Görsellerin bulunduğu klasörü seçin",
    "dlg.select_image": "Görsel seçin",
    "dlg.choose_input": "Girdi seçin",
    "dlg.folder_or_file": "Tüm klasör dönüştürülsün mü?\n\nEvet — klasör seçin\nHayır — tek görsel seçin",
    "dlg.select_out_folder": "Çıktı klasörünü seçin",
    "dlg.save_pdf": "PDF'yi farklı kaydet",
    "dlg.save_docx": "Word belgesini farklı kaydet",
    "dlg.save_txt": "Metin dosyasını farklı kaydet",
    "dlg.save_image": "Görseli farklı kaydet",
    "dlg.folder_not_empty": "Klasör boş değil",
    "dlg.folder_not_empty_body": "{path}\n\nAynı adlı dosyaların üzerine yazılacak. Devam edilsin mi?",
    "dlg.overwrite_file": "Üzerine yazılsın mı?",
    "dlg.overwrite_file_body": "{path}\n\nBu dosya değiştirilsin mi?",
    "dlg.cannot_run": "Çalıştırılamıyor",
    "dlg.failed": "Dönüştürme başarısız",
    "filetype.images": "Görseller",
    "filetype.pdf": "PDF",
    "filetype.word": "Word",
    "filetype.text": "Metin",
    "filetype.image": "Görsel",

    # ---- engine errors
    "err.no_images": "Hiç görsel bulunamadı.",
    "err.input_required": "Bir girdi yolu seçin.",
    "err.output_required": "Bir çıktı yolu seçin.",
    "err.input_missing": "Girdi yolu bulunamadı:\n{path}",
    "err.input_docx": "Girdi bir .docx dosyası olmalı.",
    "err.input_pdf": "Girdi bir .pdf dosyası olmalı.",
    "err.input_folder": "Girdi bir klasör olmalı.",
    "err.input_image": "Girdi bir görsel dosyası olmalı.",
    "err.output_folder_expected": ("Bu dönüştürme birden çok dosya oluşturur, bu yüzden çıktı bir "
                                   "klasör olmalı.\n'{name}' bir dosya gibi görünüyor."),
    "err.output_image_ext": "Çıktı görseli .png veya .jpg olmalı",
    "err.merge_empty": "Birleştirme listesi boş — önce PDF ekleyin.",
    "err.dpi_range": "DPI 72 ile 600 arasında olmalı.",
    "err.format_png_jpg": "Biçim png veya jpg olmalı.",
    "err.choose_out_format": "Şu biçimlerden birini seçin: {formats}",
    "err.whole_number": "{field} tam sayı olmalı ('{value}' girildi).",
    "err.page_range": "'{part}' sayfa aralığı okunamadı. Örnek: tümü, 1-3,7,10-",
    "err.no_pages": "Hiç sayfa seçilmedi.",
    "err.no_pages_or_images": "Hiç sayfa seçilmedi (ya da resim içeren sayfa yok).",
    "err.unsupported_format": "Desteklenmeyen çıktı biçimi: {fmt}",
    "err.save_failed": (".{fmt} olarak kaydedilemedi. Pillow sürümünüz bu biçimi "
                        "desteklemiyor olabilir.\nAyrıntı: {details}"),
    "err.ranges_required": "1-3,4-7 biçiminde aralık girin",
    "err.ranges_format": "Aralıklar 1-3,4-7 biçiminde olmalı",
    "err.range_unreadable": "'{block}' aralığı okunamadı.",
    "err.no_pdfs": "Hiç PDF seçilmedi.",
    "err.no_docx_in_folder": "Klasörde .docx dosyası bulunamadı.",
    "err.no_subfolders": "Alt klasör bulunamadı. Görselleri alt klasörlere koyun.",
    "err.image_no_size": "Görselin boyutu yok: {path}",
    "err.unknown_mode": "Bilinmeyen işlem: {key}",
    "err.word_unavailable": ("Word → PDF kullanılamıyor. {why}\n\n"
                             "Bu dönüştürme Microsoft Word'ü çalıştırır; Word'ün bu bilgisayarda "
                             "kurulu ve lisanslı olması gerekir."),
    "err.pdf2docx_missing": ("PDF → Word için 'pdf2docx' paketi gerekir.\n"
                             "Şu komutla kurun:  pip install pdf2docx\nAyrıntı: {details}"),
    "err.pythondocx_missing": ("Görseller → Word için 'python-docx' paketi gerekir.\n"
                               "Şu komutla kurun:  pip install python-docx\nAyrıntı: {details}"),
    "err.pdf_to_word_failed": "PDF → Word başarısız: {details}",
    "why.not_windows": "Word dönüştürmesi için Windows üzerinde Microsoft Word gerekir.",
    "why.no_docx2pdf": "'docx2pdf' paketi kurulu değil.",
    "why.no_word": "Microsoft Word kurulu görünmüyor.",
    "why.word_ok": "Microsoft Word bulundu.",

    # ---- engine progress messages
    "msg.saved": "Kaydedildi: {path}",
    "msg.created": "Oluşturuldu: {path}",
    "msg.added": "Eklendi: {path}",
    "msg.found_images": "{count} görsel bulundu. PDF oluşturuluyor...",
    "msg.word_to_pdf": "Word → PDF (Microsoft Word çalıştırılıyor)...",
    "msg.created_clean": "Oluşturuldu (temizle/sıkıştır): {path}",
    "msg.created_rebuild": "Oluşturuldu ({dpi} dpi ile yeniden): {path}",
    "msg.pdf_no_text_layer": ("Not: bu PDF'de metin katmanı yok (büyük olasılıkla tarama). "
                              "Çıktıda düzenlenebilir metin değil, sayfa görselleri olacak."),
    "msg.converting_pages": "{count} sayfa Word'e dönüştürülüyor — bu biraz sürebilir...",
}

TRANSLATIONS: dict[str, dict[str, str]] = {
    "en": EN,
    "tr": TR,
}
