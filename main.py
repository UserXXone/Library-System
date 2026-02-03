import multiprocessing
import sys
import os

# =============================================================================
# 1. KRİTİK FREN SİSTEMİ: BU SATIRLAR EN ÜSTTE OLMALI
# =============================================================================
if __name__ == '__main__':
    multiprocessing.freeze_support()

import sqlite3
from tkinter import *
from tkinter import ttk, messagebox, filedialog, scrolledtext
import subprocess
from datetime import datetime

# ================= KÜTÜPHANE KONTROLÜ VE YÜKLEME =================
def install_and_import(package):
    try:
        return __import__(package)
    except ImportError:
        # EXE içindeysek ASLA pip çalıştırma
        if getattr(sys, 'frozen', False):
            print(f"[EXE MODE] {package} bulunamadı ama yükleme atlandı.")
            return None

        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", package
            ])
            return __import__(package)
        except Exception as e:
            print(f"Hata: {package} yüklenemedi -> {e}")
            return None

tkcalendar = install_and_import("tkcalendar")
if tkcalendar:
    from tkcalendar import DateEntry

pd = install_and_import("pandas")
openpyxl = install_and_import("openpyxl")

# ================= GLOBAL DEĞİŞKENLER (BAŞLANGIÇTA BOŞ) =================
# HATA DÜZELTİLDİ: Veritabanı bağlantısı burada yapılmıyor.
# Sadece değişken yerleri ayrılıyor.
conn = None
cur = None
root = None
tree = None
search_entry = None
clock_id = None
console_window = None
console_text = None

# ================= LOGLAMA VE KONSOL SİSTEMİ (ALT+2) =================
class ConsoleRedirector:
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, str_val):
        try:
            if self.text_widget and self.text_widget.winfo_exists():
                self.text_widget.config(state=NORMAL)
                self.text_widget.insert(END, str_val)
                self.text_widget.see(END)
                self.text_widget.config(state=DISABLED)
                if root: root.update_idletasks()
        except: pass

    def flush(self): pass

def log_msg(message):
    timestamp = datetime.now().strftime("[%H:%M:%S]")
    print(f"{timestamp} {message}")

def toggle_console(event=None):
    global console_window, console_text
    
    if console_window is not None and console_window.winfo_exists():
        console_window.destroy()
        console_window = None
        return

    console_window = Toplevel(root)
    console_window.title("Sistem Yönetim Konsolu (Debug Mode)")
    console_window.geometry("800x500")
    console_window.configure(bg="#0c0c0c")
    
    header = Label(console_window, text=">>> SYSTEM KERNEL MONITORING STREAM", bg="#0c0c0c", fg="#00ff00", font=("Consolas", 11, "bold"))
    header.pack(anchor=W, padx=5, pady=5)
    
    console_text = scrolledtext.ScrolledText(console_window, bg="#0c0c0c", fg="#00ff00", font=("Consolas", 9), state=DISABLED)
    console_text.pack(fill=BOTH, expand=True, padx=5, pady=5)
    
    sys.stdout = ConsoleRedirector(console_text)
    sys.stderr = ConsoleRedirector(console_text)
    
    log_msg("Konsol başlatıldı. Sistem dinleniyor...")
    log_msg(f"Process ID: {os.getpid()}")

# ================= HACK MODE / ROOT ACCESS (CTRL+2) =================
def open_hack_mode(event=None):
    h_win = Toplevel(root)
    h_win.title("ROOT ACCESS GRANTED (HACK MODE)")
    h_win.geometry("900x700")
    h_win.configure(bg="black")
    
    style_lbl = {"bg": "black", "fg": "#ff0000", "font": ("Courier New", 16, "bold")}
    style_btn = {"bg": "#330000", "fg": "#ff0000", "font": ("Courier New", 10, "bold"), "bd": 1, "relief": RIDGE}

    Label(h_win, text="⚠️ YETKİSİZ ERİŞİM TESPİT EDİLDİ ⚠️", **style_lbl).pack(pady=20)
    Label(h_win, text="ADMINISTRATOR LEVEL 99 - DATABASE OVERRIDE", bg="black", fg="white", font=("Courier New", 10)).pack()

    # --- SQL ENJEKTÖRÜ ---
    frame_sql = LabelFrame(h_win, text="SQL INJECTOR", bg="black", fg="green", font=("Arial", 10, "bold"))
    frame_sql.pack(fill=BOTH, expand=True, padx=20, pady=20)
    
    txt_sql = Text(frame_sql, height=5, bg="#111", fg="#0f0", insertbackground="white", font=("Consolas", 11))
    txt_sql.pack(fill=X, padx=10, pady=10)
    txt_sql.insert(END, "SELECT * FROM books") 

    result_txt = Text(frame_sql, bg="black", fg="yellow", height=12, state=DISABLED, font=("Consolas", 9))
    
    def run_sql():
        query = txt_sql.get("1.0", END).strip()
        if not query: return
        
        try:
            cur.execute(query)
            if query.lower().startswith("select"):
                rows = cur.fetchall()
                result_txt.config(state=NORMAL); result_txt.delete("1.0", END)
                result_txt.insert(END, f"Sorgu Başarılı. Kayıt: {len(rows)}\n" + "="*60 + "\n")
                for r in rows: result_txt.insert(END, str(r) + "\n")
                result_txt.config(state=DISABLED)
            else:
                conn.commit()
                result_txt.config(state=NORMAL); result_txt.delete("1.0", END)
                result_txt.insert(END, f"KOMUT İŞLENDİ (COMMIT).\nEtkilenen: {cur.rowcount}")
                result_txt.config(state=DISABLED)
                refresh_books() 
                log_msg(f"SQL ÇALIŞTIRILDI: {query}")
        except Exception as e:
            result_txt.config(state=NORMAL); result_txt.delete("1.0", END)
            result_txt.insert(END, f"SQL HATASI:\n{str(e)}")
            result_txt.config(state=DISABLED)

    Button(frame_sql, text="EXECUTE RAW SQL (ÇALIŞTIR)", command=run_sql, **style_btn).pack(fill=X, padx=10)
    result_txt.pack(fill=BOTH, expand=True, padx=10, pady=10)

    # --- TEHLİKELİ BUTONLAR ---
    frame_tools = Frame(h_win, bg="black")
    frame_tools.pack(fill=X, padx=20, pady=20)

    def force_return_all():
        if messagebox.askyesno("Hack Mode", "DİKKAT: Ödünçteki TÜM kitapları 'İade Edildi' sayayım mı?"):
            cur.execute("UPDATE loans SET returned=1")
            cur.execute("UPDATE books SET available=1")
            conn.commit(); refresh_books()
            log_msg("HACK: Tüm kitaplar zorla iade alındı.")
            messagebox.showinfo("Hack", "Operasyon Tamamlandı.")

    def create_ghost():
        try:
            cur.execute("INSERT INTO users (numara, name, role) VALUES ('ghost', 'GHOST ADMIN', 'admin')")
            conn.commit()
            log_msg("HACK: Ghost Admin oluşturuldu.")
            messagebox.showinfo("Hack", "Kullanıcı: ghost\nAdı: GHOST ADMIN\nRol: admin")
        except: messagebox.showerror("Hata", "Ghost zaten var.")

    def nuke_db():
        if messagebox.askyesno("KRİTİK UYARI", "TÜM VERİTABANI SİLİNECEK!\n\nBu işlem geri alınamaz. Emin misin?"):
            cur.execute("DELETE FROM books"); cur.execute("DELETE FROM users"); cur.execute("DELETE FROM loans")
            cur.execute("INSERT INTO users (numara, name, role) VALUES ('admin', 'Yönetici', 'admin')")
            conn.commit(); refresh_books()
            log_msg("HACK: VERİTABANI SIFIRLANDI (NUKE).")
            messagebox.showwarning("Wiped", "Veritabanı temizlendi.")

    Button(frame_tools, text="[FORCE RETURN ALL]", command=force_return_all, width=20, **style_btn).pack(side=LEFT, padx=5)
    Button(frame_tools, text="[CREATE GHOST USER]", command=create_ghost, width=20, **style_btn).pack(side=LEFT, padx=5)
    Button(frame_tools, text="[NUKE DATABASE]", command=nuke_db, width=20, bg="#ff0000", fg="white", font=("Arial", 9, "bold")).pack(side=RIGHT, padx=5)

# ================= VERİTABANI BAĞLANTISI (DÜZELTİLDİ) =================
def setup_database():
    # Bu fonksiyon artık sadece çağrıldığında çalışacak, globalde değil.
    # Bu sayede sonsuz döngü engelleniyor.
    global conn, cur
    conn = sqlite3.connect("kutuphane.db")
    cur = conn.cursor()
    
    cur.execute("""CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, numara TEXT UNIQUE, name TEXT, role TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS books (id INTEGER PRIMARY KEY AUTOINCREMENT, isbn TEXT, title TEXT, author TEXT, barcode TEXT UNIQUE, shelf TEXT, category TEXT, available INTEGER DEFAULT 1)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS loans (id INTEGER PRIMARY KEY AUTOINCREMENT, book_id INTEGER, user_id INTEGER, borrow_date TEXT, return_date TEXT, returned INTEGER DEFAULT 0)""")
    
    try:
        cur.execute("INSERT OR IGNORE INTO users (numara, name, role) VALUES ('admin', 'Yönetici', 'admin')")
        conn.commit()
    except: pass

# ================= GLOBAL AYARLAR VE DİL =================
CURRENT_LANG = "TR"
CURRENT_THEME = "Modern Koyu"

LANGS = {
    "TR": {
        "title": "Kütüphane Yönetim Sistemi (vFinal Ultra)",
        "sidebar_title": "YÖNETİM\nPANELİ",
        "search": "Hızlı Arama (Ad/Barkod):",
        "btn_barcode": "📦 Barkod Sorgula",
        "btn_loans": "⚠️ Gecikenler / Durum",
        "btn_borrow": "📕 Ödünç Ver",
        "btn_return": "📗 İade Al",
        "btn_add": "➕ Kitap Ekle",
        "btn_import": "📥 Excel'den Yükle",
        "btn_export": "📤 Excel'e Kaydet",
        "btn_student": "🎓 Öğrenci İşlemleri",
        "btn_exit": "❌ Kapat",
        "col_id": "ID", "col_title": "KİTAP ADI", "col_author": "YAZAR",
        "col_barcode": "BARKOD/QR", "col_shelf": "RAF", "col_status": "DURUM",
        "col_student": "ÖĞRENCİ", "col_no": "NUMARA", "col_date": "İADE TARİHİ",
        "succ_title": "Başarılı", "err_title": "Hata",
        "excel_info": "Sistem Excel dosyasındaki TÜM sayfaları tarar.\nBarkodlardaki .0 uzantılarını temizler.\nRafları BÜYÜK HARFE çevirir.\nKitap varsa ve raf bilgisi yeniyse günceller.",
        "succ_import": "İşlem Tamamlandı!\n\n✅ Eklenen: {}\n🔄 Güncellenen (Raf): {}\n⚠️ Atlanan: {}"
    },
    "EN": {
        "title": "Library Management System",
        "sidebar_title": "ADMIN\nPANEL",
        "search": "Quick Search (Name/Barcode):",
        "btn_barcode": "📦 Barcode Scan",
        "btn_loans": "⚠️ Overdue / Status",
        "btn_borrow": "📕 Borrow Book",
        "btn_return": "📗 Return Book",
        "btn_add": "➕ Add Book",
        "btn_import": "📥 Import Excel",
        "btn_export": "📤 Export to Excel",
        "btn_student": "🎓 Student Ops",
        "btn_exit": "❌ Exit",
        "col_id": "ID", "col_title": "BOOK TITLE", "col_author": "AUTHOR",
        "col_barcode": "BARCODE", "col_shelf": "SHELF", "col_status": "STATUS",
        "col_student": "STUDENT", "col_no": "NUMBER", "col_date": "DUE DATE",
        "succ_title": "Success", "err_title": "Error",
        "excel_info": "System scans all sheets.\nCleans .0 decimals.\nConverts shelves to UPPERCASE.\nUpdates shelf if book exists.",
        "succ_import": "Done!\n\n✅ Added: {}\n🔄 Updated: {}\n⚠️ Skipped: {}"
    }
}

THEMES = {
    "Modern Koyu": {"side": "#2c3e50", "side_fg": "white", "bg": "#ecf0f1", "btn": "#34495e", "accent": "#1abc9c", "txt": "#2c3e50"},
    "Gece Modu": {"side": "#121212", "side_fg": "#e0e0e0", "bg": "#1e1e1e", "btn": "#333333", "accent": "#bb86fc", "txt": "#e0e0e0"},
    "Okyanus": {"side": "#0277bd", "side_fg": "white", "bg": "#e1f5fe", "btn": "#01579b", "accent": "#00b0ff", "txt": "#01579b"}
}

# ================= YARDIMCI FONKSİYONLAR =================
def center_window(win, w=300, h=200):
    ws = win.winfo_screenwidth(); hs = win.winfo_screenheight()
    win.geometry('%dx%d+%d+%d' % (w, h, (ws/2)-(w/2), (hs/2)-(h/2)))

def exit_app():
    if messagebox.askyesno("Çıkış", "Uygulamadan çıkmak istiyor musunuz?"): root.destroy()

def copy_to_clipboard(text):
    root.clipboard_clear(); root.clipboard_append(text); log_msg(f"Kopyalandı: {text}")

# ================= ANA EKRAN VE DASHBOARD =================
def main_screen():
    global root
    
    # VERİTABANI BAĞLANTISINI BURADA YAPIYORUZ
    setup_database()
    
    root = Tk()
    root.title(LANGS[CURRENT_LANG]["title"])
    root.geometry("1400x850")
    
    # --- KISAYOLLAR ---
    root.bind('<Alt-KeyPress-2>', toggle_console) # Konsol
    root.bind('<Control-KeyPress-2>', open_hack_mode) # Hack Modu
    
    render_dashboard()
    print("Sistem boot edildi. Güvenlik protokolleri aktif.")
    root.mainloop()

def render_dashboard():
    global tree, search_entry, clock_id
    for widget in root.winfo_children(): widget.destroy()

    t = THEMES[CURRENT_THEME]
    l = LANGS[CURRENT_LANG]
    root.configure(bg=t["bg"])

    # --- SIDEBAR ---
    side = Frame(root, bg=t["side"], width=260)
    side.pack(side=LEFT, fill=Y)
    side.pack_propagate(False)

    Label(side, text=l["sidebar_title"], bg=t["side"], fg=t["side_fg"], font=("Arial", 20, "bold")).pack(pady=40)

    # Ayarlar
    ctrl = Frame(side, bg=t["side"])
    ctrl.pack(fill=X, padx=20, pady=10)
    
    l_cb = ttk.Combobox(ctrl, values=["TR", "EN"], state="readonly"); l_cb.set(CURRENT_LANG); l_cb.pack(fill=X, pady=(0, 10))
    l_cb.bind("<<ComboboxSelected>>", lambda e: [globals().update(CURRENT_LANG=l_cb.get()), render_dashboard()])

    t_cb = ttk.Combobox(ctrl, values=list(THEMES.keys()), state="readonly"); t_cb.set(CURRENT_THEME); t_cb.pack(fill=X)
    t_cb.bind("<<ComboboxSelected>>", lambda e: [globals().update(CURRENT_THEME=t_cb.get()), render_dashboard()])

    # Butonlar
    btn_style = {"bg": t["side"], "fg": "white", "activebackground": t["accent"], "font": ("Segoe UI", 10), "bd": 0, "height": 2, "anchor": W, "padx": 20}
    
    menus = [
        (l["btn_barcode"], barcode_query),
        (l["btn_loans"], loan_status),
        (l["btn_borrow"], borrow_book),
        (l["btn_return"], return_book),
        (l["btn_add"], add_book_window),
        (l["btn_import"], import_excel),
        (l["btn_export"], export_excel),
        (l["btn_student"], student_ops),
        (l["btn_exit"], exit_app)
    ]

    for txt, cmd in menus:
        Button(side, text=txt, command=cmd, **btn_style).pack(fill=X, pady=1)

    # Saat
    clk_frm = Frame(side, bg=t["side"])
    clk_frm.pack(side=BOTTOM, fill=X, pady=30, padx=20)
    lbl_clk = Label(clk_frm, text="", font=("Impact", 24), bg=t["side"], fg=t["accent"]); lbl_clk.pack(anchor=W)
    lbl_dt = Label(clk_frm, text="", font=("Arial", 9), bg=t["side"], fg="white"); lbl_dt.pack(anchor=W)

    def update_clock():
        global clock_id
        if not lbl_clk.winfo_exists(): return
        now = datetime.now()
        lbl_clk.config(text=now.strftime("%H:%M:%S"))
        lbl_dt.config(text=now.strftime("%d %B %Y\n%A"))
        clock_id = root.after(1000, update_clock)
    update_clock()

    # --- MAIN CONTENT ---
    main = Frame(root, bg=t["bg"], padx=20, pady=20)
    main.pack(side=RIGHT, expand=True, fill=BOTH)

    s_frm = Frame(main, bg=t["bg"])
    s_frm.pack(fill=X, pady=(0, 15))
    Label(s_frm, text=l["search"], bg=t["bg"], fg=t["txt"], font=("Arial", 12, "bold")).pack(side=LEFT)
    search_entry = Entry(s_frm, font=("Arial", 12), bd=1, relief=SOLID)
    search_entry.pack(side=LEFT, fill=X, expand=True, padx=15, ipady=5)
    search_entry.bind("<KeyRelease>", lambda e: refresh_books())

    # Tablo
    tree_frame = Frame(main)
    tree_frame.pack(expand=True, fill=BOTH)
    
    cols = ("id", "title", "author", "barcode", "shelf", "status")
    tree = ttk.Treeview(tree_frame, columns=cols, show="headings")
    
    h_map = [l["col_id"], l["col_title"], l["col_author"], l["col_barcode"], l["col_shelf"], l["col_status"]]
    for c, h in zip(cols, h_map):
        tree.heading(c, text=h); tree.column(c, width=120)
    
    tree.pack(side=LEFT, expand=True, fill=BOTH)
    sc = ttk.Scrollbar(tree_frame, orient=VERTICAL, command=tree.yview); sc.pack(side=RIGHT, fill=Y); tree.configure(yscrollcommand=sc.set)

    # Sağ Tık
    ctx = Menu(root, tearoff=0)
    ctx.add_command(label="📋 Barkodu Kopyala", command=lambda: copy_to_clipboard(tree.item(tree.selection())['values'][3]))
    ctx.add_command(label="📖 Adı Kopyala", command=lambda: copy_to_clipboard(tree.item(tree.selection())['values'][1]))
    ctx.add_separator()
    ctx.add_command(label="✏️ Düzenle", command=edit_book)
    ctx.add_command(label="🗑️ Sil", command=delete_book)
    tree.bind("<Button-3>", lambda e: [tree.selection_set(tree.identify_row(e.y)), ctx.tk_popup(e.x_root, e.y_root)] if tree.identify_row(e.y) else None)
    
    refresh_books()

# ================= İŞLEVLER (CRUD & EXCEL) =================
def refresh_books():
    if cur is None: return
    q = search_entry.get()
    tree.delete(*tree.get_children())
    cur.execute("SELECT id, title, author, barcode, shelf, available FROM books WHERE title LIKE ? OR barcode LIKE ? OR author LIKE ?", (f'%{q}%', f'%{q}%', f'%{q}%'))
    for r in cur.fetchall(): tree.insert("", END, values=(*r[:5], "Mevcut" if r[5] else "Ödünçte"))

def add_book_window():
    l = LANGS[CURRENT_LANG]
    win = Toplevel(); win.title(l["btn_add"]); center_window(win, 350, 420)
    fields = [("isbn", "ISBN"), ("title", "Kitap Adı"), ("author", "Yazar"), ("barcode", "Barkod/QR"), ("shelf", "Raf (Örn: C2)")]
    ents = {}
    for db_col, lbl in fields:
        Label(win, text=lbl).pack(pady=(10,0))
        e = Entry(win, font=("Arial", 10)); e.pack(padx=20, fill=X); ents[db_col] = e
        
    def save():
        try:
            if not ents["barcode"].get().strip(): messagebox.showerror(l["err_title"], "Barkod zorunludur!"); return
            shf = ents["shelf"].get().strip().upper()
            vals = [ents["isbn"].get(), ents["title"].get(), ents["author"].get(), ents["barcode"].get(), shf]
            cur.execute("INSERT INTO books (isbn, title, author, barcode, shelf) VALUES (?,?,?,?,?)", vals)
            conn.commit(); refresh_books(); win.destroy()
            log_msg(f"Yeni kitap eklendi: {vals[1]}")
            messagebox.showinfo(l["succ_title"], "Kitap Eklendi")
        except sqlite3.IntegrityError: 
            log_msg("Hata: Mükerrer barkod")
            messagebox.showerror(l["err_title"], "Bu barkod kayıtlı!")
    Button(win, text="KAYDET", bg="#2980b9", fg="white", command=save, height=2).pack(pady=20, padx=20, fill=X)

def edit_book():
    sel = tree.selection()
    if not sel: return
    bid = tree.item(sel[0])['values'][0]
    book = cur.execute("SELECT isbn, title, author, barcode, shelf FROM books WHERE id=?", (bid,)).fetchone()
    win = Toplevel(); win.title("Düzenle"); center_window(win, 350, 400)
    ents = {}
    fields = ["isbn", "title", "author", "barcode", "shelf"]
    for i, f in enumerate(fields):
        Label(win, text=f).pack(pady=(5,0)); e = Entry(win); e.pack(padx=20, fill=X); e.insert(0, book[i]); ents[fields[i]] = e
    def update():
        try:
            shf = ents["shelf"].get().strip().upper()
            cur.execute("UPDATE books SET isbn=?, title=?, author=?, barcode=?, shelf=? WHERE id=?", 
                        (ents["isbn"].get(), ents["title"].get(), ents["author"].get(), ents["barcode"].get(), shf, bid))
            conn.commit(); refresh_books(); win.destroy()
            messagebox.showinfo("Başarılı", "Güncellendi")
        except sqlite3.IntegrityError: messagebox.showerror("Hata", "Barkod çakışması!")
    Button(win, text="GÜNCELLE", bg="#f39c12", fg="white", command=update).pack(pady=20, fill=X, padx=20)

def delete_book():
    sel = tree.selection()
    if not sel: return
    if messagebox.askyesno("Sil", "Silinsin mi?"):
        cur.execute("DELETE FROM books WHERE id=?", (tree.item(sel[0])['values'][0],))
        conn.commit(); refresh_books(); log_msg("Kitap silindi.")

def import_excel():
    if not pd: messagebox.showerror("Hata", "Pandas eksik!"); return
    l = LANGS[CURRENT_LANG]
    fp = filedialog.askopenfilename(filetypes=[("Excel", "*.xlsx;*.xls")])
    if not fp: return

    try:
        log_msg(f"Dosya okunuyor: {fp}")
        xls = pd.ExcelFile(fp)
        p_win = Toplevel(root); p_win.title("İşleniyor..."); center_window(p_win, 400, 150)
        Label(p_win, text="Veriler analiz ediliyor...", font=("Arial", 10)).pack(pady=10)
        pb = ttk.Progressbar(p_win, orient=HORIZONTAL, length=300, mode='determinate'); pb.pack(pady=10)
        lbl_count = Label(p_win, text="Hazırlanıyor..."); lbl_count.pack(); p_win.update()

        total_rows = 0
        for s in xls.sheet_names: total_rows += len(pd.read_excel(xls, sheet_name=s))
        
        added, updated, skipped, current = 0, 0, 0, 0
        
        col_map = {'barcode': ['qr', 'barkod', 'barcode', 'isbn', 'ısbn'], 'title': ['kitap_adi', 'kitap', 'title'], 'shelf': ['raf', 'shelf', 'demirbas'], 'isbn':['isbn'], 'author':['yazar'], 'category':['kategori']}
        def find_col(df, cands):
            for col in df.columns:
                if str(col).lower().strip() in cands: return col
            return None
        def clean_val(val):
            s = str(val).strip()
            if s.lower() == 'nan' or not s: return ""
            return s.split(".")[0] if "." in s else s

        for sheet_name in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet_name)
            c_bar, c_tit = find_col(df, col_map['barcode']), find_col(df, col_map['title'])
            c_shf, c_aut = find_col(df, col_map['shelf']), find_col(df, col_map['author'])
            c_isbn, c_cat = find_col(df, col_map['isbn']), find_col(df, col_map['category'])

            if not c_bar and not c_tit: current += len(df); continue

            for _, row in df.iterrows():
                try:
                    current += 1
                    barcode = clean_val(row[c_bar]) if c_bar else ""
                    title = str(row[c_tit]).strip() if c_tit and pd.notna(row[c_tit]) else ""
                    author = str(row[c_aut]).strip() if c_aut and pd.notna(row[c_aut]) else ""
                    shelf = clean_val(row[c_shf]).upper() if c_shf else ""
                    isbn = clean_val(row[c_isbn]) if c_isbn else ""
                    cat = str(row[c_cat]).strip() if c_cat and pd.notna(row[c_cat]) else ""
                    
                    if not barcode and isbn: barcode = isbn
                    if not barcode or not title or barcode.lower() == 'nan': skipped += 1
                    else:
                        try:
                            cur.execute("INSERT INTO books (isbn, title, author, barcode, shelf, category) VALUES (?,?,?,?,?,?)", (isbn, title, author, barcode, shelf, cat))
                            added += 1
                        except sqlite3.IntegrityError:
                            if shelf: 
                                cur.execute("UPDATE books SET shelf=? WHERE barcode=?", (shelf, barcode))
                                updated += 1
                            else: skipped += 1
                except: skipped += 1
                if current % 10 == 0: pb['value'] = (current / total_rows) * 100; lbl_count.config(text=f"{current} / {total_rows}"); p_win.update()

        p_win.destroy(); conn.commit(); refresh_books()
        messagebox.showinfo(l["succ_title"], l["succ_import"].format(added, updated, skipped))
    except Exception as e:
        if 'p_win' in locals(): p_win.destroy()
        messagebox.showerror(l["err_title"], str(e))

def export_excel():
    if not pd: return
    l = LANGS[CURRENT_LANG]
    fp = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")])
    if not fp: return
    try:
        df = pd.read_sql_query("SELECT isbn, title, author, barcode, shelf, category, available FROM books", conn)
        df['available'] = df['available'].apply(lambda x: 'MEVCUT' if x else 'ÖDÜNÇTE')
        df.columns = ['ISBN', 'KİTAP ADI', 'YAZAR', 'BARKOD/QR', 'RAF', 'KATEGORİ', 'DURUM']
        df.to_excel(fp, index=False)
        messagebox.showinfo(l["succ_title"], "Kaydedildi.")
    except Exception as e: messagebox.showerror(l["err_title"], str(e))

def student_ops():
    l = LANGS[CURRENT_LANG]
    win = Toplevel(); win.title(l["btn_student"]); center_window(win, 650, 500)
    def refresh_std(tree_ref):
        tree_ref.delete(*tree_ref.get_children())
        cur.execute("SELECT id, numara, name FROM users WHERE role='ogrenci'")
        for r in cur.fetchall(): tree_ref.insert("", END, values=r)
    def std_form(data=None, tree_ref=None):
        f = Toplevel(); center_window(f, 300, 250); f.title(l["btn_student"])
        Label(f, text=l["col_no"]).pack(pady=5); en = Entry(f); en.pack(); en.insert(0, data[1] if data else "")
        Label(f, text=l["col_student"]).pack(pady=5); ea = Entry(f); ea.pack(); ea.insert(0, data[2] if data else "")
        def save():
            no, name = en.get().strip(), ea.get().strip()
            if not no or not name: messagebox.showerror("Hata", "Boş alan!"); return
            try:
                if data: cur.execute("UPDATE users SET numara=?, name=? WHERE id=?", (no, name, data[0]))
                else: cur.execute("INSERT INTO users (numara, name, role) VALUES (?,?,'ogrenci')", (no, name))
                conn.commit(); refresh_std(tree_ref); f.destroy()
                messagebox.showinfo("Başarılı", "Kaydedildi")
            except sqlite3.IntegrityError: messagebox.showerror("Hata", l["err_unique_user"])
        Button(f, text="KAYDET", command=save, bg="#3498db", fg="white", pady=5).pack(pady=20)
    
    btn_frm = Frame(win, pady=10); btn_frm.pack(fill=X)
    stree = ttk.Treeview(win, columns=("id", "no", "name"), show="headings")
    stree.heading("id", text="ID"); stree.heading("no", text=l["col_no"]); stree.heading("name", text=l["col_student"])
    stree.pack(fill=BOTH, expand=True, padx=15, pady=15)
    Button(btn_frm, text="➕ Öğrenci Ekle", bg="#27ae60", fg="white", command=lambda: std_form(None, stree)).pack(side=LEFT, padx=15)
    m = Menu(win, tearoff=0)
    m.add_command(label="Düzenle", command=lambda: std_form(stree.item(stree.selection())['values'], stree))
    m.add_command(label="Sil", command=lambda: [cur.execute("DELETE FROM users WHERE id=?", (stree.item(stree.selection())['values'][0],)), conn.commit(), refresh_std(stree)])
    stree.bind("<Button-3>", lambda e: [stree.selection_set(stree.identify_row(e.y)), m.tk_popup(e.x_root, e.y_root)] if stree.identify_row(e.y) else None)
    refresh_std(stree)

def borrow_book():
    l = LANGS[CURRENT_LANG]
    win = Toplevel(); win.title(l["btn_borrow"]); center_window(win, 300, 300)
    Label(win, text="Barkod").pack(); eb = Entry(win); eb.pack(pady=5)
    Label(win, text="Öğrenci No").pack(); eu = Entry(win); eu.pack(pady=5)
    cal = DateEntry(win, date_pattern='yyyy-mm-dd'); cal.pack(pady=10)
    sel = tree.selection()
    if sel: eb.insert(0, tree.item(sel[0])['values'][3])
    def do():
        b = cur.execute("SELECT id FROM books WHERE barcode=? AND available=1", (eb.get().strip(),)).fetchone()
        u = cur.execute("SELECT id FROM users WHERE numara=?", (eu.get().strip(),)).fetchone()
        if b and u:
            cur.execute("INSERT INTO loans (book_id, user_id, borrow_date, return_date) VALUES (?,?,?,?)", (b[0], u[0], datetime.now().strftime("%Y-%m-%d"), cal.get()))
            cur.execute("UPDATE books SET available=0 WHERE id=?", (b[0],))
            conn.commit(); refresh_books(); win.destroy()
            messagebox.showinfo(l["succ_title"], "Verildi")
        else: messagebox.showerror(l["err_title"], "Hata: Kitap ödünçte veya öğrenci yok.")
    Button(win, text="ONAYLA", bg="#27ae60", fg="white", command=do).pack(pady=10)

def return_book():
    l = LANGS[CURRENT_LANG]
    win = Toplevel(); win.title(l["btn_return"]); center_window(win, 300, 150)
    Label(win, text="Barkod").pack(pady=5); e = Entry(win, font=("Arial", 12)); e.pack(); e.focus()
    def do():
        b = cur.execute("SELECT id FROM books WHERE barcode=?", (e.get().strip(),)).fetchone()
        if b:
            cur.execute("UPDATE loans SET returned=1 WHERE book_id=? AND returned=0", (b[0],))
            cur.execute("UPDATE books SET available=1 WHERE id=?", (b[0],))
            conn.commit(); refresh_books(); win.destroy()
            messagebox.showinfo(l["succ_title"], "İade alındı.")
        else: messagebox.showerror(l["err_title"], "Kayıt yok")
    Button(win, text="İADE AL", bg="#e74c3c", fg="white", command=do).pack(pady=10)

def barcode_query():
    win = Toplevel(); win.title("Sorgu"); center_window(win, 300, 150)
    e = Entry(win, font=("Arial", 14)); e.pack(pady=20, padx=20); e.focus()
    def q(ev):
        r = cur.execute("SELECT title, shelf, available FROM books WHERE barcode=?", (e.get().strip(),)).fetchone()
        if r: messagebox.showinfo("Bilgi", f"Kitap: {r[0]}\nRaf: {r[1]}\nDurum: {'Mevcut' if r[2] else 'Ödünçte'}")
        else: messagebox.showwarning("!", "Bulunamadı")
    e.bind("<Return>", q)

def loan_status():
    win = Toplevel(); win.geometry("900x400")
    l = LANGS[CURRENT_LANG]
    lt = ttk.Treeview(win, columns=(1,2,3,4,5), show="headings")
    for i, h in enumerate([l["col_title"], l["col_student"], l["col_no"], l["col_date"], l["col_status"]], 1): lt.heading(i, text=h)
    lt.tag_configure('late', background='#ffcccc'); lt.tag_configure('warn', background='#fff3cd')
    lt.pack(fill=BOTH, expand=True)
    today = datetime.now().strftime("%Y-%m-%d")
    for r in cur.execute("SELECT b.title, u.name, u.numara, l.return_date FROM loans l JOIN books b ON b.id=l.book_id JOIN users u ON u.id=l.user_id WHERE l.returned=0").fetchall():
        tag = 'late' if r[3] < today else ('warn' if r[3] == today else '')
        status = "GECİKTİ" if r[3] < today else ("BUGÜN" if r[3] == today else "Normal")
        lt.insert("", END, values=(*r, status), tags=(tag,))

# ================= BAŞLAT =================
if __name__ == "__main__":
    # Windows'ta sonsuz döngüyü engelleyen temel fren
    multiprocessing.freeze_support()
    
    # Ana ekran fonksiyonunu sadece burada çağırıyoruz
    main_screen()