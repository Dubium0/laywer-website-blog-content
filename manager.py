import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
import git
import datetime
import re
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import shutil

# --- Configuration ---
REPO_PATH = "." 
POSTS_METADATA_DIR = os.path.join(REPO_PATH, "_metadata") 
CATEGORIES_FILE = os.path.join(REPO_PATH, "_categories.json")
IMAGES_DIR = os.path.join(REPO_PATH, "_images") 

# These files will be generated during the publish process
FINAL_MD_DIR = REPO_PATH 
FINAL_INDEX_FILE = os.path.join(REPO_PATH, "_index.json")


# --- Main Application: Dashboard ---
class Dashboard(ttk.Window):
    def __init__(self):
        super().__init__(themename="litera")
        self.title("Website İçerik Yöneticisi")
        self.geometry("800x600")

        # --- Style Configuration ---
        self.style.configure('TButton', font=('Lato', 10))
        self.style.configure('TLabel', font=('Lato', 10))
        self.style.configure('Treeview.Heading', font=('Lora', 11, 'bold'))
        self.style.configure('primary.TButton', font=('Lato', 11, 'bold'))

        # --- Data ---
        os.makedirs(POSTS_METADATA_DIR, exist_ok=True)
        os.makedirs(IMAGES_DIR, exist_ok=True)
        self.repo = git.Repo(REPO_PATH)

        # --- UI ---
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.columnconfigure(0, weight=3)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)

        # Left Panel: Article List
        list_frame = ttk.LabelFrame(main_frame, text="Makale Listesi", padding=10)
        list_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 20))
        
        self.tree = ttk.Treeview(list_frame, columns=("title", "category", "status"), show="headings")
        self.tree.heading("title", text="Makale Başlığı")
        self.tree.heading("category", text="Kategori")
        self.tree.heading("status", text="Durum")
        self.tree.column("category", width=150, anchor=tk.CENTER)
        self.tree.column("status", width=100, anchor=tk.CENTER)
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_item_select)

        # Right Panel: Action Buttons
        actions_frame = ttk.LabelFrame(main_frame, text="İşlemler", padding=20)
        actions_frame.grid(row=0, column=1, sticky="nsew")

        self.new_button = ttk.Button(actions_frame, text="Yeni Makale Ekle", command=self.open_article_editor, bootstyle="success")
        self.new_button.pack(pady=10, fill=tk.X)

        self.edit_button = ttk.Button(actions_frame, text="Seçili Makaleyi Düzenle", command=self.open_article_editor_for_edit, state=tk.DISABLED)
        self.edit_button.pack(pady=10, fill=tk.X)
        
        self.delete_button = ttk.Button(actions_frame, text="Seçili Makaleyi Sil", command=self.delete_article, bootstyle="danger", state=tk.DISABLED)
        self.delete_button.pack(pady=10, fill=tk.X)

        # Bottom Section: Global Actions
        global_actions_frame = ttk.Frame(self, padding=(20, 10))
        global_actions_frame.pack(fill=tk.X)

        ttk.Button(global_actions_frame, text="Kategorileri Yönet", command=self.open_category_manager, bootstyle="secondary").pack(side=tk.LEFT)
        ttk.Button(global_actions_frame, text="DEĞİŞİKLİKLERİ YAYINLA", command=self.publish_changes, bootstyle="primary").pack(side=tk.RIGHT)

        self.refresh_article_list()

    def on_item_select(self, event=None):
        if self.tree.selection():
            self.edit_button.config(state=tk.NORMAL)
            self.delete_button.config(state=tk.NORMAL)
        else:
            self.edit_button.config(state=tk.DISABLED)
            self.delete_button.config(state=tk.DISABLED)

    def refresh_article_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        changed_files = {item.a_path for item in self.repo.index.diff(None)}
        untracked_files = set(self.repo.untracked_files)
        local_changes = changed_files.union(untracked_files)

        for filename in sorted(os.listdir(POSTS_METADATA_DIR)):
            if filename.endswith(".json"):
                with open(os.path.join(POSTS_METADATA_DIR, filename), 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                status = "Yayınlandı"
                if f"_metadata/{filename}" in local_changes:
                    status = "Taslak"

                self.tree.insert("", tk.END, values=(data["title"], data["category"], status), iid=data["slug"])
        self.on_item_select()

    def open_article_editor(self):
        ArticleEditor(self, "Yeni Makale Ekle", None, self.refresh_article_list)

    def open_article_editor_for_edit(self):
        if not self.tree.selection(): return
        slug = self.tree.selection()[0]
        ArticleEditor(self, "Makaleyi Düzenle", slug, self.refresh_article_list)

    def delete_article(self):
        if not self.tree.selection(): return
        slug = self.tree.selection()[0]
        title = self.tree.item(slug, "values")[0]

        if messagebox.askyesno("Onay", f"'{title}' başlıklı makaleyi kalıcı olarak silmek istediğinizden emin misiniz?"):
            json_path = os.path.join(POSTS_METADATA_DIR, f"{slug}.json")
            if os.path.exists(json_path): os.remove(json_path)
            self.refresh_article_list()
            messagebox.showinfo("Başarılı", f"'{title}' silindi. Değişikliği yansıtmak için yayınlayın.")

    def open_category_manager(self):
        CategoryManager(self)

    def publish_changes(self):
        if not messagebox.askyesno("Yayınlama Onayı", "Bu işlem, web sitesini yaptığınız son değişikliklerle güncelleyecektir. Bu, geri alınamaz. Devam etmek istediğinizden emin misiniz?"):
            return
        
        try:
            remote_url = self.repo.remotes.origin.url
            if remote_url.endswith('.git'): remote_url = remote_url[:-4]
            if remote_url.startswith("git@github.com:"): remote_url = remote_url.replace("git@github.com:", "https://github.com/")
            raw_content_url = remote_url.replace("https://github.com/", "https://raw.githubusercontent.com/") + "/main"
        except Exception as e:
            messagebox.showerror("Hata", f"GitHub repo URL'si alınamadı: {e}")
            return
            
        all_posts_metadata_for_index = []
        
        for filename in sorted(os.listdir(POSTS_METADATA_DIR)):
            if filename.endswith(".json"):
                filepath = os.path.join(POSTS_METADATA_DIR, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Copy the final markdown content to the root for publishing
                shutil.copy(data['md_path'], os.path.join(FINAL_MD_DIR, f"{data['slug']}.md"))
                
                # Prepare metadata for the final _index.json
                metadata = {k: v for k, v in data.items() if k not in ['md_path', 'image_repo_path']}
                metadata['image_url'] = f"{raw_content_url}/{data['image_repo_path']}"
                with open(data['md_path'], 'r', encoding='utf-8') as md_f:
                    content = md_f.read()
                    metadata['excerpt'] = " ".join(content.split()[:25]) + "..."

                all_posts_metadata_for_index.append(metadata)
        
        all_posts_metadata_for_index.sort(key=lambda p: datetime.datetime.strptime(p['date'], "%d %B %Y"), reverse=True)
        with open(FINAL_INDEX_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_posts_metadata_for_index, f, indent=2, ensure_ascii=False)
        
        try:
            self.repo.git.add(A=True)
            if not self.repo.is_dirty(untracked_files=True):
                messagebox.showinfo("Bilgi", "Yayınlanacak yeni değişiklik bulunmuyor.")
                return
            
            self.repo.index.commit(f"Content update via CMS: {datetime.datetime.now().isoformat()}")
            self.repo.remote(name='origin').push()
            self.refresh_article_list()
            messagebox.showinfo("İşlem Başarılı", "Web sitesi başarıyla güncellendi!")
        except Exception as e:
            messagebox.showerror("Hata Oluştu", f"Website güncellenirken bir hata oluştu.\nHata detayı: {e}")

# --- Article Editor Window ---
class ArticleEditor(ttk.Toplevel):
    def __init__(self, parent, title, slug=None, callback=None):
        super().__init__(parent)
        self.title(title)
        self.geometry("600x400")
        self.parent = parent
        self.slug = slug
        self.callback = callback
        
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.columnconfigure(1, weight=1)

        ttk.Label(main_frame, text="Makale Başlığı:").grid(row=0, column=0, sticky="w", pady=5)
        self.title_entry = ttk.Entry(main_frame)
        self.title_entry.grid(row=0, column=1, sticky="ew", pady=5)

        ttk.Label(main_frame, text="Kategori:").grid(row=1, column=0, sticky="w", pady=5)
        self.category_combobox = ttk.Combobox(main_frame, state="readonly")
        self.category_combobox.grid(row=1, column=1, sticky="ew", pady=5)
        self.load_categories()

        ttk.Label(main_frame, text="Kapak Görseli:").grid(row=2, column=0, sticky="w", pady=5)
        self.image_repo_path = tk.StringVar()
        image_frame = ttk.Frame(main_frame)
        image_frame.grid(row=2, column=1, sticky="ew", pady=5)
        self.image_entry = ttk.Entry(image_frame, textvariable=self.image_repo_path, state="readonly")
        self.image_entry.pack(side=tk.LEFT, expand=True, fill=tk.X)
        ttk.Button(image_frame, text="Görsel Seç...", command=self.browse_image, bootstyle="secondary").pack(side=tk.RIGHT, padx=(5,0))

        # --- Simplified Markdown File Input ---
        ttk.Label(main_frame, text="Makale Dosyası (.md):").grid(row=3, column=0, sticky="w", pady=5)
        self.md_path_var = tk.StringVar()
        md_frame = ttk.Frame(main_frame)
        md_frame.grid(row=3, column=1, sticky="ew", pady=5)
        self.md_entry = ttk.Entry(md_frame, textvariable=self.md_path_var, state="readonly")
        self.md_entry.pack(side=tk.LEFT, expand=True, fill=tk.X)
        ttk.Button(md_frame, text="Markdown Seç...", command=self.browse_md, bootstyle="secondary").pack(side=tk.RIGHT, padx=(5,0))
        
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, columnspan=2, pady=(20, 0))
        ttk.Button(button_frame, text="Kaydet", command=self.save_article, bootstyle="success").pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="İptal", command=self.cancel, bootstyle="secondary").pack(side=tk.LEFT)

        if self.slug:
            self.load_article_data()

    def load_categories(self):
        try:
            with open(CATEGORIES_FILE, 'r', encoding='utf-8') as f:
                self.category_combobox['values'] = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.category_combobox['values'] = []

    def load_article_data(self):
        filepath = os.path.join(POSTS_METADATA_DIR, f"{self.slug}.json")
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.title_entry.insert(0, data["title"])
            self.category_combobox.set(data["category"])
            self.image_repo_path.set(data.get("image_repo_path", "Lütfen bir görsel seçin"))
            self.md_path_var.set(data.get("md_path", "Lütfen bir markdown dosyası seçin"))
        except FileNotFoundError:
            messagebox.showerror("Hata", "Makale verisi bulunamadı.")
            self.destroy()

    def browse_image(self):
        filepath = filedialog.askopenfilename(title="Kapak Görseli Seç", filetypes=(("Image Files", "*.jpg *.jpeg *.png"),))
        if filepath:
            filename = os.path.basename(filepath)
            dest_path = os.path.join(IMAGES_DIR, filename)
            shutil.copy(filepath, dest_path)
            self.image_repo_path.set(os.path.join("_images", filename).replace("\\", "/"))

    def browse_md(self):
        filepath = filedialog.askopenfilename(title="Makale Markdown Dosyası Seç", filetypes=(("Markdown Files", "*.md"),))
        if filepath:
            self.md_path_var.set(filepath)

    def save_article(self):
        title = self.title_entry.get().strip()
        category = self.category_combobox.get()
        md_path = self.md_path_var.get()
        image_repo_path = self.image_repo_path.get()

        if not all([title, category, md_path, image_repo_path]) or "Lütfen" in md_path or "Lütfen" in image_repo_path:
            messagebox.showerror("Hata", "Tüm alanlar doldurulmalıdır.")
            return

        if self.slug is None: 
            self.slug = self.create_slug(title)
            if os.path.exists(os.path.join(POSTS_METADATA_DIR, f"{self.slug}.json")):
                messagebox.showerror("Hata", "Bu başlığa sahip bir makale zaten mevcut.")
                self.slug = None 
                return
        
        data = {
            "slug": self.slug,
            "title": title,
            "category": category,
            "date": datetime.datetime.now().strftime("%d %B %Y"),
            "md_path": md_path,
            "image_repo_path": image_repo_path,
        }

        with open(os.path.join(POSTS_METADATA_DIR, f"{self.slug}.json"), 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        if self.callback: self.callback()
        self.destroy()
    
    def cancel(self):
        if messagebox.askyesno("Onay", "Kaydedilmemiş değişiklikler var. Çıkmak istediğinize emin misiniz?"):
            self.destroy()

    def create_slug(self, title):
        s = title.lower()
        s = s.replace('ı', 'i').replace('ö', 'o').replace('ü', 'u').replace('ş', 's').replace('ç', 'c').replace('ğ', 'g')
        s = re.sub(r'[^\w\s-]', '', s)
        s = re.sub(r'[\s_-]+', '-', s).strip('-')
        return s

# --- Category Manager Window ---
class CategoryManager(ttk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Kategorileri Yönet")
        self.geometry("400x400")
        
        self.load_categories()

        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        list_frame = ttk.LabelFrame(main_frame, text="Mevcut Kategoriler", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0,20))
        self.cat_listbox = tk.Listbox(list_frame)
        self.cat_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.delete_button = ttk.Button(list_frame, text="Sil", command=self.delete_category, bootstyle="danger")
        self.delete_button.pack(side=tk.LEFT, padx=(10,0), anchor="n")

        add_frame = ttk.LabelFrame(main_frame, text="Yeni Kategori Ekle", padding=10)
        add_frame.pack(fill=tk.X)
        self.add_entry = ttk.Entry(add_frame)
        self.add_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(add_frame, text="Ekle", command=self.add_category, bootstyle="success").pack(side=tk.LEFT, padx=(10,0))

        ttk.Button(self, text="Kapat", command=self.destroy, bootstyle="secondary").pack(pady=(10,0))
        self.refresh_listbox()
    
    def load_categories(self):
        try:
            with open(CATEGORIES_FILE, 'r', encoding='utf-8') as f:
                self.categories = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.categories = []

    def save_categories(self):
        with open(CATEGORIES_FILE, 'w', encoding='utf-8') as f:
            json.dump(sorted(self.categories), f, indent=2, ensure_ascii=False)
    
    def refresh_listbox(self):
        self.cat_listbox.delete(0, tk.END)
        for cat in sorted(self.categories):
            self.cat_listbox.insert(tk.END, cat)

    def add_category(self):
        new_cat = self.add_entry.get().strip()
        if new_cat and new_cat not in self.categories:
            self.categories.append(new_cat)
            self.save_categories()
            self.refresh_listbox()
            self.add_entry.delete(0, tk.END)
        else:
            messagebox.showwarning("Uyarı", "Kategori boş olamaz veya zaten mevcut.")

    def delete_category(self):
        selection = self.cat_listbox.curselection()
        if not selection: return
        selected_cat = self.cat_listbox.get(selection[0])
        if messagebox.askyesno("Onay", f"'{selected_cat}' kategorisini silmek istediğinize emin misiniz? Bu kategorideki makaleler etkilenmez, ancak kategori listesinden kaldırılır."):
            self.categories.remove(selected_cat)
            self.save_categories()
            self.refresh_listbox()

if __name__ == "__main__":
    app = Dashboard()
    app.mainloop()
