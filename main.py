import multiprocessing
import sys
import os

if __name__ == '__main__':
    multiprocessing.freeze_support()

import sqlite3
from tkinter import *
from tkinter import ttk, messagebox, filedialog, scrolledtext
import subprocess

# ================= KÜTÜPHANE YÜKLEME =================
def install_and_import(package):
    try:
        return __import__(package)
    except ImportError:
        if getattr(sys, 'frozen', False): 
            return None
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            return __import__(package)
        except: 
            return None

pd = install_and_import("pandas")
openpyxl = install_and_import("openpyxl")
tkcalendar = install_and_import("tkcalendar")
if tkcalendar: 
    from tkcalendar import DateEntry

# ================= GLOBAL DEĞİŞKENLER =================
conn = None
cur = None
root = None
tree = None
search_entry = None
console_window = None

# ================= VERİTABANI =================
def setup_database():
    global conn, cur
    conn = sqlite3.connect("kutuphane.db")
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS books (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, author TEXT, barcode TEXT UNIQUE, shelf TEXT, category TEXT, available INTEGER DEFAULT 1)")
    cur.execute("CREATE TABLE IF NOT EXISTS loans (id INTEGER PRIMARY KEY AUTOINCREMENT, book_id INTEGER, user_id INTEGER, borrow_date TEXT, return_date TEXT, returned INTEGER DEFAULT 0)")
    cur.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, numara TEXT UNIQUE, name TEXT, role TEXT)")
    conn.commit()

# ================= YARDIMCI FONKSİYONLAR =================
def clean_value(val):
    v = str(val).strip()
    if v.lower() == 'nan' or v == '': 
        return ""
    if v.endswith('.0'): 
        return v[:-2]
    return v

# ================= IMPORT MOTORU (OPTİMİZE EDİLMİŞ) =================
def import_excel():
    if not pd: 
        messagebox.showerror("Hata", "Pandas kütüphanesi yüklenemedi!")
        return
    
    fp = filedialog.askopenfilename(title="Dosya Seç (Excel veya CSV)", filetypes=[("Tüm Dosyalar", "*.*")])
    if not fp: 
        return

    try:
        p_win = Toplevel(root)
        p_win.title("Yükleniyor...")
        ws = p_win.winfo_screenwidth()
        hs = p_win.winfo_screenheight()
        p_win.geometry(f'400x150+{(ws//2)-200}+{(hs//2)-75}')
        
        Label(p_win, text="Veriler İşleniyor...", font=("Arial", 12, "bold")).pack(pady=10)
        pb = ttk.Progressbar(p_win, length=300, mode='determinate')
        pb.pack(pady=5)
        lbl_info = Label(p_win, text="Hazırlanıyor...")
        lbl_info.pack()
        p_win.update()

        df = None
        if fp.lower().endswith('.csv'):
            for kodlama in ['utf-8', 'cp1254', 'iso-8859-1']:
                try:
                    df = pd.read_csv(fp, dtype=str, encoding=kodlama, sep=None, engine='python')
                    break
                except: 
                    continue
        else:
            df = pd.read_excel(fp, dtype=str)

        if df is None:
            p_win.destroy()
            messagebox.showerror("Hata", "Dosya formatı desteklenmiyor veya bozuk!")
            return

        df.columns = [str(c).strip().upper() for c in df.columns]

        col_qr = None
        col_title = None
        col_author = None
        col_shelf = None

        for p in ['QR', 'BARKOD', 'BARCODE']:
            if p in df.columns: 
                col_qr = p
                break
        
        if not col_qr and 'ISBN' in df.columns: 
            col_qr = 'ISBN'

        for c in df.columns:
            if c in ['KITAP_ADI', 'KITAP ADI', 'KITAP', 'TITLE', 'ESER ADI']: 
                col_title = c
            elif c in ['YAZAR', 'AUTHOR']: 
                col_author = c
            elif c in ['RAF', 'SHELF', 'DEMIRBAS', 'YER']: 
                col_shelf = c

        if not col_qr or not col_title:
            p_win.destroy()
            messagebox.showerror("Hata", f"Gerekli sütunlar bulunamadı!\nAranan: QR/ISBN ve KITAP_ADI\nBulunanlar: {list(df.columns)}")
            return

        total = len(df)
        added, updated, skipped = 0, 0, 0
        
        insert_query = "INSERT INTO books (title, author, barcode, shelf) VALUES (?,?,?,?)"
        update_query = "UPDATE books SET shelf=? WHERE barcode=?"

        for i, row in df.iterrows():
            try:
                barcode = clean_value(row[col_qr])
                title = clean_value(row[col_title])
                author = clean_value(row[col_author]) if col_author else ""
                shelf = clean_value(row[col_shelf]).upper() if col_shelf else ""

                if not barcode or not title:
                    skipped += 1
                    continue

                try:
                    cur.execute(insert_query, (title, author, barcode, shelf))
                    added += 1
                except sqlite3.IntegrityError:
                    if shelf:
                        cur.execute(update_query, (shelf, barcode))
                        updated += 1
                    else:
                        skipped += 1
            except: 
                skipped += 1
            
            if i % 100 == 0:
                pb['value'] = (i / total) * 100
                lbl_info.config(text=f"{i}/{total}")
                p_win.update()

        conn.commit()
        p_win.destroy()
        refresh_books()
        messagebox.showinfo("Sonuç", f"✅ Eklendi: {added}\n🔄 Güncellendi: {updated}\n⚠️ Atlandı: {skipped}")

    except Exception as e:
        if 'p_win' in locals(): 
            p_win.destroy()
        messagebox.showerror("Hata", str(e))

def export_excel():
    fp = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")])
    if fp:
        try:
            pd.read_sql_query("SELECT * FROM books", conn).to_excel(fp, index=False)
            messagebox.showinfo("Tamam", "Veriler başarıyla kaydedildi.")
        except Exception as e: 
            messagebox.showerror("Hata", str(e))

# ================= ARAYÜZ FONKSİYONLARI =================
def refresh_books():
    if not cur: 
        return
    q = search_entry.get().strip()
    tree.delete(*tree.get_children())
    
    query = "SELECT id, title, author, barcode, shelf, available FROM books WHERE title LIKE ? OR barcode LIKE ? OR author LIKE ?"
    params = (f'%{q}%', f'%{q}%', f'%{q}%')
    
    cur.execute(query, params)
    for r in cur.fetchall():
        durum = "Mevcut" if r[5] else "Ödünçte"
        tree.insert("", END, values=(r[0], r[1], r[2], r[3], r[4], durum))

# ================= DEBUG VE HACK MODLARI =================
def toggle_console(event=None):
    global console_window
    if console_window: 
        console_window.destroy()
        console_window = None
        return
    console_window = Toplevel(root)
    console_window.title("Sistem İzleme Konsolu")
    console_window.geometry("600x400")
    console_window.configure(bg="black")
    txt = scrolledtext.ScrolledText(console_window, bg="black", fg="#00ff00", font=("Consolas", 10))
    txt.pack(fill=BOTH, expand=True, padx=5, pady=5)
    txt.insert(END, ">>> SİSTEM KONSOLU AKTİF\n")
    txt.config(state=DISABLED)

def open_hack_mode(event=None):
    h = Toplevel(root)
    h.title("ROOT ACCESS")
    h.geometry("500x300")
    h.configure(bg="black")
    Label(h, text=">>> SQL INJECTOR <<<", fg="#00ff00", bg="black", font=("Consolas", 14, "bold")).pack(pady=10)
    t = Text(h, height=5, bg="#111", fg="#00ff00", font=("Consolas", 11), insertbackground="white")
    t.pack(fill=X, padx=10)
    
    def run():
        try:
            cur.execute(t.get("1.0", END).strip())
            conn.commit()
            refresh_books()
            messagebox.showinfo("Başarılı", "SQL komutu işlendi.")
        except Exception as e: 
            messagebox.showerror("Hata", str(e))
            
    Button(h, text="SORGULA / ÇALIŞTIR", command=run, bg="#005500", fg="#00ff00", font=("Consolas", 10, "bold")).pack(pady=15)

# ================= ANA EKRAN =================
def main_screen():
    global root, tree, search_entry
    setup_database()
    
    root = Tk()
    root.title("Kütüphane Sistemi - Stabil Sürüm")
    root.geometry("1200x700")
    
    # Kısayollar
    root.bind('<Alt-KeyPress-2>', toggle_console)
    root.bind('<Control-KeyPress-2>', open_hack_mode)

    # Üst Kısım
    top = Frame(root, bg="#2c3e50", pady=15)
    top.pack(fill=X)
    Label(top, text="🔍 Hızlı Ara:", bg="#2c3e50", fg="white", font=("Arial", 12, "bold")).pack(side=LEFT, padx=15)
    search_entry = Entry(top, font=("Arial", 12))
    search_entry.pack(side=LEFT, fill=X, expand=True, padx=15)
    search_entry.bind("<KeyRelease>", lambda e: refresh_books())

    # Tablo
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("Treeview", font=("Arial", 10), rowheight=25)
    style.configure("Treeview.Heading", font=("Arial", 10, "bold"))

    cols = ("ID", "Kitap Adı", "Yazar", "Barkod / QR", "Raf", "Durum")
    tree = ttk.Treeview(root, columns=cols, show="headings")
    for col in cols: 
        tree.heading(col, text=col)
    
    tree.column("ID", width=50)
    tree.column("Kitap Adı", width=350)
    tree.column("Yazar", width=200)
    tree.column("Barkod / QR", width=150)
    tree.column("Raf", width=100)
    tree.column("Durum", width=100)
    
    sc = ttk.Scrollbar(root, orient=VERTICAL, command=tree.yview)
    tree.configure(yscrollcommand=sc.set)
    tree.pack(side=TOP, fill=BOTH, expand=True, padx=15, pady=10)
    sc.place(in_=tree, relx=1.0, relheight=1.0, bordermode="outside")

    # Alt Butonlar
    bot = Frame(root, pady=15)
    bot.pack(fill=X)
    btn_conf = {'font': ('Arial', 10, 'bold'), 'padx': 20, 'pady': 8, 'bd': 0}
    
    Button(bot, text="📥 EXCEL/CSV YÜKLE", bg="#27ae60", fg="white", command=import_excel, **btn_conf).pack(side=LEFT, padx=15)
    Button(bot, text="📤 EXCEL İNDİR", bg="#2980b9", fg="white", command=export_excel, **btn_conf).pack(side=LEFT, padx=15)
    Button(bot, text="🔄 YENİLE", bg="#f39c12", fg="white", command=refresh_books, **btn_conf).pack(side=LEFT, padx=15)

    refresh_books()
    root.mainloop()

if __name__ == "__main__":
    main_screen()
