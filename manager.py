import tkinter as tk
from tkinter import filedialog, messagebox
import json
import os
import fitz  # PyMuPDF
import git
import datetime
import re
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

# --- Configuration ---
REPO_PATH = "."
INDEX_FILE = os.path.join(REPO_PATH, "_index.json")

class BlogManager(ttk.Window):
    def __init__(self):
        # Initialize with a custom theme that matches the website
        super().__init__(themename="litera") 

        self.title("Avukat Blog İçerik Yöneticisi")
        self.geometry("900x600")

        # --- Custom Style Configuration ---
        self.style.configure('TButton', font=('Lato', 10))
        self.style.configure('TLabel', font=('Lato', 10))
        self.style.configure('TEntry', font=('Lato', 10))
        self.style.configure('TFrame')
        self.style.configure('TLabelframe.Label', font=('Lora', 12, 'bold'))
        
        # Define custom button styles based on website palette
        self.style.configure('primary.TButton', background='#1d3557', foreground='white')
        self.style.map('primary.TButton', background=[('active', '#344966')])
        
        self.style.configure('warning.TButton', background='#c9a227', foreground='white')
        self.style.map('warning.TButton', background=[('active', '#e0b445')])
        
        self.style.configure('success.TButton', background='#4CAF50', foreground='white')
        self.style.map('success.TButton', background=[('active', '#66BB6A')])

        # --- Data ---
        self.posts_data = []
        try:
            self.repo = git.Repo(REPO_PATH)
        except git.exc.InvalidGitRepositoryError:
            messagebox.showerror("Hata", "Bu dizin bir Git deposu değil. Lütfen doğru klasöre yerleştirdiğinizden emin olun.")
            self.destroy()
            return

        # --- UI Elements ---
        self.main_frame = ttk.Frame(self, padding="15")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Left side: Post List
        list_frame = ttk.LabelFrame(self.main_frame, text="Mevcut Makaleler", padding="10")
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 15))

        self.post_listbox = tk.Listbox(list_frame, font=('Lato', 11), borderwidth=0, highlightthickness=0)
        self.post_listbox.pack(fill=tk.BOTH, expand=True)
        self.post_listbox.bind("<<ListboxSelect>>", self.on_post_select)

        # Right side: Form
        form_frame = ttk.LabelFrame(self.main_frame, text="Makale Detayları", padding="15")
        form_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        form_frame.columnconfigure(1, weight=1)

        # Form fields
        ttk.Label(form_frame, text="Başlık:").grid(row=0, column=0, sticky="w", pady=5)
        self.title_entry = ttk.Entry(form_frame, width=40)
        self.title_entry.grid(row=0, column=1, sticky="ew", pady=5)

        ttk.Label(form_frame, text="Kategori:").grid(row=1, column=0, sticky="w", pady=5)
        self.category_entry = ttk.Entry(form_frame, width=40)
        self.category_entry.grid(row=1, column=1, sticky="ew", pady=5)

        ttk.Label(form_frame, text="PDF Dosyası:").grid(row=2, column=0, sticky="w", pady=5)
        self.pdf_path_var = tk.StringVar()
        pdf_frame = ttk.Frame(form_frame)
        pdf_frame.grid(row=2, column=1, sticky="ew", pady=5)
        ttk.Entry(pdf_frame, textvariable=self.pdf_path_var, state="readonly").pack(side=tk.LEFT, expand=True, fill=tk.X)
        ttk.Button(pdf_frame, text="Gözat...", command=self.browse_pdf, bootstyle=SECONDARY).pack(side=tk.RIGHT, padx=(5,0))
        
        # Separator and Action Buttons
        ttk.Separator(form_frame, orient=HORIZONTAL).grid(row=3, columnspan=2, pady=20, sticky="ew")

        action_button_frame = ttk.Frame(form_frame)
        action_button_frame.grid(row=4, columnspan=2)
        
        ttk.Button(action_button_frame, text="Yeni Makale", command=self.create_new, bootstyle=SUCCESS).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_button_frame, text="Güncelle", command=self.update_post, bootstyle=INFO).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_button_frame, text="Sil", command=self.delete_post, bootstyle=DANGER).pack(side=tk.LEFT, padx=5)

        # Publish Button at the bottom
        publish_button = ttk.Button(self, text="Tüm Değişiklikleri Web Sitesine Yayınla", command=self.publish_changes, bootstyle="primary")
        publish_button.pack(fill=tk.X, padx=15, pady=10)

        # Initial Load
        self.load_posts()
        self.refresh_listbox()

    # --- Backend Logic (Functions like load_posts, save_posts, etc.) ---
    # The logic of these functions remains largely the same, but with updated messagebox styles.
    def load_posts(self):
        try:
            with open(INDEX_FILE, "r", encoding="utf-8") as f:
                self.posts_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.posts_data = []
            messagebox.showwarning("Uyarı", "_index.json dosyası bulunamadı veya bozuk. Yeni bir dosya oluşturulacak.")

    def save_posts(self):
        # Sort posts by date before saving, most recent first
        self.posts_data.sort(key=lambda p: datetime.datetime.strptime(p['date'], "%d %B %Y"), reverse=True)
        with open(INDEX_FILE, "w", encoding="utf-8") as f:
            json.dump(self.posts_data, f, indent=2, ensure_ascii=False)

    def refresh_listbox(self):
        self.post_listbox.delete(0, tk.END)
        for post in self.posts_data:
            self.post_listbox.insert(tk.END, post["title"])

    def on_post_select(self, event):
        selection_indices = self.post_listbox.curselection()
        if not selection_indices: return
        
        index = selection_indices[0]
        post = self.posts_data[index]
        
        self.title_entry.delete(0, tk.END)
        self.title_entry.insert(0, post["title"])
        self.category_entry.delete(0, tk.END)
        self.category_entry.insert(0, post["category"])
        self.pdf_path_var.set("Değiştirmek için yeni PDF seçin")

    def browse_pdf(self):
        filepath = filedialog.askopenfilename(title="PDF Dosyası Seç", filetypes=(("PDF Files", "*.pdf"),))
        if filepath: self.pdf_path_var.set(filepath)
            
    def create_slug(self, title):
        s = title.lower()
        s = s.replace('ı', 'i').replace('ö', 'o').replace('ü', 'u').replace('ş', 's').replace('ç', 'c').replace('ğ', 'g')
        s = re.sub(r'[^\w\s-]', '', s)
        s = re.sub(r'[\s_-]+', '-', s).strip('-')
        return s

    def clear_form(self):
        self.title_entry.delete(0, tk.END)
        self.category_entry.delete(0, tk.END)
        self.pdf_path_var.set("")
        self.post_listbox.selection_clear(0, tk.END)
        
    def create_new(self):
        self.clear_form()
        messagebox.showinfo("Bilgi", "Yeni makale için bilgileri girin ve 'Güncelle' butonuna basın, ardından yayınlayın.")

    def update_post(self):
        title = self.title_entry.get().strip()
        category = self.category_entry.get().strip()
        pdf_path = self.pdf_path_var.get()
        
        if not title or not category:
            messagebox.showerror("Hata", "Başlık ve Kategori alanları boş olamaz.")
            return

        selection_indices = self.post_listbox.curselection()
        # If something is selected, update it. Otherwise, create a new one.
        if selection_indices:
            index = selection_indices[0]
            self.posts_data[index]["title"] = title
            self.posts_data[index]["category"] = category
        else: # Create new post
            if not pdf_path or not os.path.exists(pdf_path):
                messagebox.showerror("Hata", "Yeni makale oluşturmak için geçerli bir PDF dosyası seçmelisiniz.")
                return
            new_post_data = {"slug": self.create_slug(title), "title": title, "category": category, "date": datetime.datetime.now().strftime("%d %B %Y")}
            self.posts_data.insert(0, new_post_data)
            index = 0
            
        # Update content if a valid PDF path is provided
        if pdf_path and os.path.exists(pdf_path):
            try:
                doc = fitz.open(pdf_path)
                content = "".join(page.get_text() for page in doc)
                doc.close()
                with open(os.path.join(REPO_PATH, f"{self.posts_data[index]['slug']}.md"), "w", encoding="utf-8") as f:
                    f.write(content)
                self.posts_data[index]["excerpt"] = " ".join(content.split()[:25]) + "..."
                self.posts_data[index]["image_url"] = "https://placehold.co/600x400/1d3557/f8f7f4?text=Makale"
            except Exception as e:
                messagebox.showerror("Hata", f"PDF okunurken hata: {e}")
                return

        self.refresh_listbox()
        messagebox.showinfo("Başarılı", f"'{title}' kaydedildi. Değişiklikleri web sitesine yansıtmak için yayınlayın.")

    def delete_post(self):
        selection_indices = self.post_listbox.curselection()
        if not selection_indices:
            messagebox.showerror("Hata", "Lütfen silmek için bir makale seçin.")
            return
        
        index = selection_indices[0]
        if messagebox.askyesno("Onay", f"'{self.posts_data[index]['title']}' başlıklı makaleyi silmek istediğinize emin misiniz?"):
            slug = self.posts_data[index]["slug"]
            md_path = os.path.join(REPO_PATH, f"{slug}.md")
            if os.path.exists(md_path): os.remove(md_path)
            self.posts_data.pop(index)
            self.refresh_listbox()
            self.clear_form()
            messagebox.showinfo("Başarılı", "Makale silindi. Değişikliği yansıtmak için yayınlayın.")

    def publish_changes(self):
        try:
            self.save_posts()
            self.repo.git.add(A=True)
            if not self.repo.is_dirty(untracked_files=True):
                messagebox.showinfo("Bilgi", "Yayınlanacak yeni değişiklik bulunmuyor.")
                return
            commit_message = f"Content update: {datetime.datetime.now().isoformat()}"
            self.repo.index.commit(commit_message)
            origin = self.repo.remote(name='origin')
            origin.push()
            messagebox.showinfo("Başarılı", "Tüm değişiklikler başarıyla yayınlandı!")
        except Exception as e:
            messagebox.showerror("Yayınlama Hatası", f"Hata: {e}\n\nİnternet bağlantınızı ve Git yapılandırmanızı kontrol edin.")

if __name__ == "__main__":
    app = BlogManager()
    app.mainloop()
