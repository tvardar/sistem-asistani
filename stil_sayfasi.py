# stil_sayfasi.py

def get_stil(tema="Koyu", vurgu_rengi="#33AADD"):
    # --- RENK PALETİ TANIMLAMALARI ---
    if tema == "Açık":
        # --- AÇIK TEMA (LIGHT MODE) ---
        c_bg = "#F0F2F5"           # Ana Arka Plan (Hafif Gri)
        c_panel = "#FFFFFF"        # Panel/Kutu Arka Planı (Beyaz)
        c_text = "#333333"         # Ana Metin (Koyu Gri)
        c_subtext = "#666666"      # Alt Metin
        c_border = "#CCCCCC"       # Kenarlıklar
        c_accent = vurgu_rengi     # Seçilen Vurgu Rengi
        c_hover = "#E5E7EB"        # Üzerine Gelince
        
        # Girdi Alanları (Tablo, Liste, Konsol, Input)
        c_input_bg = "#FFFFFF"     # Beyaz Zemin
        c_input_text = "#000000"   # Siyah Yazı
        c_header_bg = "#E9ECEF"    # Tablo Başlıkları
        
        # Konsol/Log Ekranları için özel
        c_console_bg = "#F8F9FA"
        c_console_text = "#2C3E50"

    else:
        # --- KOYU TEMA (DARK MODE - VARSAYILAN) ---
        c_bg = "#1E1E1E"
        c_panel = "#252526"
        c_text = "#E0E0E0"
        c_subtext = "#AAAAAA"
        c_border = "#3E3E42"
        c_accent = vurgu_rengi
        c_hover = "#333333"
        
        # Girdi Alanları
        c_input_bg = "#2D2D30"
        c_input_text = "#F0F0F0"
        c_header_bg = "#252526"
        
        # Konsol
        c_console_bg = "#1e1e1e"
        c_console_text = "#ccc"

    # --- CSS (STYLESHEET) ---
    return f"""
    /* GENEL PENCERE VE WIDGET AYARLARI */
    QMainWindow, QWidget {{ 
        background-color: {c_bg}; 
        color: {c_text}; 
        font-family: "Segoe UI", sans-serif; 
        font-size: 10pt; 
    }}

    /* KAYDIRMA ALANLARI (SCROLL AREA) */
    QScrollArea {{
        background-color: transparent;
        border: none;
    }}
    QScrollArea > QWidget > QWidget {{
        background-color: transparent;
    }}
    
    /* YAN MENÜ YAPISI */
    QScrollArea#YanMenuScroll {{ 
        background-color: {c_panel}; 
        border: none; 
        border-right: 1px solid {c_border}; 
    }}
    QWidget#YanMenu {{ 
        background-color: {c_panel}; 
        border: none; 
    }}

    /* STANDART BUTONLAR */
    QPushButton {{ 
        background-color: {c_panel}; 
        color: {c_text}; 
        border: 1px solid {c_border}; 
        padding: 8px 16px; 
        border-radius: 6px; 
    }}
    QPushButton:hover {{ 
        background-color: {c_hover}; 
        border-color: {c_accent}; 
    }}
    QPushButton:pressed {{
        background-color: {c_accent};
        color: #FFFFFF;
    }}
    QPushButton:disabled {{
        color: {c_subtext};
        background-color: {c_bg};
        border-color: {c_border};
    }}
    
    /* YAN MENÜ BUTONLARI (Özel ID) */
    QPushButton#MenuDugmesi {{ 
        background-color: transparent; 
        color: {c_subtext}; 
        border: none; 
        padding: 12px 20px; 
        text-align: left; 
        border-radius: 0px; 
        border-left: 4px solid transparent; 
    }}
    QPushButton#MenuDugmesi:hover {{ 
        background-color: {c_hover}; 
        color: {c_text}; 
    }}
    QPushButton#MenuDugmesi:checked {{ 
        background-color: {c_hover}; 
        color: {c_accent}; 
        font-weight: bold; 
        border-left: 4px solid {c_accent}; 
    }}

    /* GRUP KUTULARI (GROUP BOX) */
    QGroupBox {{ 
        background-color: {c_panel}; 
        border: 1px solid {c_border}; 
        border-radius: 8px; 
        margin-top: 30px; /* Başlık için yer */
        font-weight: bold; 
        color: {c_accent}; 
        padding-top: 15px;
    }}
    QGroupBox::title {{ 
        subcontrol-origin: margin; 
        subcontrol-position: top left; 
        padding: 0 5px; 
        left: 15px; 
        top: 5px;
        background-color: transparent;
    }}

    /* GİRDİ ALANLARI (TEXT, LIST, TREE, TABLE) */
    QLineEdit, QListWidget, QTableWidget, QTreeWidget, QTextEdit {{ 
        background-color: {c_input_bg}; 
        border: 1px solid {c_border}; 
        color: {c_input_text}; 
        border-radius: 4px; 
        gridline-color: {c_border}; 
        selection-background-color: {c_accent};
        selection-color: #FFFFFF;
    }}
    
    /* COMBOBOX (AÇILIR MENÜ) */
    QComboBox {{
        background-color: {c_input_bg};
        color: {c_input_text};
        border: 1px solid {c_border};
        border-radius: 4px;
        padding: 6px;
        min-height: 20px;
    }}
    QComboBox:hover {{
        border-color: {c_accent};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 20px;
    }}
    /* Açılır listenin kendisi */
    QComboBox QAbstractItemView {{
        background-color: {c_input_bg};
        color: {c_input_text};
        selection-background-color: {c_accent};
        selection-color: #FFFFFF;
        border: 1px solid {c_border};
        outline: none;
    }}

    /* CHECKBOX */
    QCheckBox {{
        color: {c_text};
        spacing: 8px;
        font-size: 10pt;
    }}
    QCheckBox::indicator {{
        width: 18px;
        height: 18px;
        border: 1px solid {c_border};
        border-radius: 3px;
        background-color: {c_input_bg};
    }}
    QCheckBox::indicator:hover {{
        border-color: {c_accent};
    }}
    QCheckBox::indicator:checked {{
        background-color: {c_accent};
        border-color: {c_accent};
        image: url(none); 
    }}
    /* Checked olduğunda içi dolu görünsün diye bir trick */
    QCheckBox::indicator:checked:hover {{
        background-color: {c_accent}; 
        border: 1px solid {c_accent};
    }}

    /* TIME EDIT (SAAT SEÇİMİ) */
    QTimeEdit {{
        background-color: {c_input_bg};
        color: {c_input_text};
        border: 1px solid {c_border};
        border-radius: 4px;
        padding: 4px;
    }}

    /* TABLO BAŞLIKLARI */
    QHeaderView::section {{ 
        background-color: {c_header_bg}; 
        color: {c_text}; 
        padding: 6px; 
        border: none; 
        font-weight: bold; 
        border-bottom: 1px solid {c_border}; 
        border-right: 1px solid {c_border};
    }}
    QHeaderView::section:last {{
        border-right: none;
    }}

    /* PROGRESS BAR */
    QProgressBar {{ 
        background-color: {c_bg}; 
        border: 1px solid {c_border}; 
        border-radius: 4px; 
        text-align: center; 
        color: {c_text}; 
    }}
    QProgressBar::chunk {{ 
        background-color: {c_accent}; 
        border-radius: 3px; 
    }}

    /* SEKME YAPISI (TAB WIDGET) */
    QTabWidget::pane {{ 
        border: 1px solid {c_border}; 
        background-color: {c_panel};
        border-radius: 4px;
    }}
    QTabBar::tab {{ 
        background: {c_bg}; 
        color: {c_text}; 
        padding: 10px 20px; 
        border: 1px solid {c_border}; 
        border-bottom: none; 
        margin-right: 2px; 
        border-top-left-radius: 4px; 
        border-top-right-radius: 4px; 
    }}
    QTabBar::tab:selected {{ 
        background: {c_panel}; 
        color: {c_accent}; 
        font-weight: bold; 
        border-bottom: 2px solid {c_panel}; /* Panelle birleşmesi için */
    }}
    QTabBar::tab:hover {{
        background-color: {c_hover};
    }}

    /* SAYFA BAŞLIĞI ÇERÇEVESİ */
    QFrame#SayfaBasligi {{ 
        background-color: {c_panel}; 
        border-bottom: 2px solid {c_border}; 
        border-radius: 8px; 
    }}
    QLabel#BaslikMetni {{ 
        color: {c_accent}; 
        font-size: 22pt; 
        font-weight: 300; 
    }}
    
    /* ÖZEL KONSOLLAR */
    QTextEdit#LogEkrani, QListWidget#LogListesi {{
        font-family: "Monospace", "Consolas", "Courier New";
        background-color: {c_console_bg};
        color: {c_console_text};
    }}
    """