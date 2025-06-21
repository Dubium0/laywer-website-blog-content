import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os
import fitz  # PyMuPDF
import git
import datetime
import re

# --- Configuration ---
REPO_PATH = "."  # Assumes the script is in the root of the content repo
INDEX_FILE = os.path.join(REPO_PATH, "_index.json")

class BlogManager(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Avukat Blog İçerik Yöneticisi")
        self.geometry("800x500")

        # --- Data ---
        self.posts_data = []
        self.repo = git.Repo(REPO_PATH)

        # --- UI Elements ---
        self.main_frame = ttk.Frame(self, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Left side: Post List
        list_frame = ttk.LabelFrame(self.main_frame, text="Mevcut Makaleler", padding="10")
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        self.post_listbox = tk.Listbox(list_frame)
        self.post_listbox.pack(fill=tk.BOTH, expand=True)
        self.post_listbox.bind("<<ListboxSelect>>", self.on_post_select)

        # Right side: Form
        form_frame = ttk.LabelFrame(self.main_frame, text="Makale Detayları", padding="10")
        form_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        ttk.Label(form_frame, text="Başlık:").grid(row=0, column=0, sticky="w", pady=2)
        self.title_entry = ttk.Entry(form_frame, width=40)
        self.title_entry.grid(row=0, column=1, sticky="ew", pady=2)

        ttk.Label(form_frame, text="Kategori:").grid(row=1, column=0, sticky="w", pady=2)
        self.category_entry = ttk.Entry(form_frame, width=40)
        self.category_entry.grid(row=1, column=1, sticky="ew", pady=2)

        ttk.Label(form_frame, text="PDF Dosyası:").grid(row=2, column=0, sticky="w", pady=2)
        self.pdf_path_var = tk.StringVar()
        pdf_frame = ttk.Frame(form_frame)
        pdf_frame.grid(row=2, column=1, sticky="ew", pady=2)
        ttk.Entry(pdf_frame, textvariable=self.pdf_path_var, state="readonly").pack(side=tk.LEFT, expand=True, fill=tk.X)
        ttk.Button(pdf_frame, text="Gözat...", command=self.browse_pdf).pack(side=tk.RIGHT)

        # Action Buttons
        button_frame = ttk.Frame(self, padding="10")
        button_frame.pack(fill=tk.X)

        ttk.Button(button_frame, text="Yeni Makale Oluştur", command=self.create_new).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Seçili Makaleyi Güncelle", command=self.update_post).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Seçili Makaleyi Sil", command=self.delete_post).pack(side=tk.LEFT, padx=5)
        
        publish_button = ttk.Button(button_frame, text="Değişiklikleri Yayınla", command=self.publish_changes, style="Accent.TButton")
        publish_button.pack(side=tk.RIGHT, padx=5)
        
        self.style = ttk.Style(self)
        self.style.configure("Accent.TButton", foreground="white", background="green")

        # Initial Load
        self.load_posts()
        self.refresh_listbox()

    def load_posts(self):
        try:
            with open(INDEX_FILE, "r", encoding="utf-8") as f:
                self.posts_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.posts_data = []
            messagebox.showwarning("Uyarı", "_index.json dosyası bulunamadı veya bozuk. Yeni bir dosya oluşturulacak.")

    def save_posts(self):
        with open(INDEX_FILE, "w", encoding="utf-8") as f:
            json.dump(self.posts_data, f, indent=2, ensure_ascii=False)

    def refresh_listbox(self):
        self.post_listbox.delete(0, tk.END)
        for post in self.posts_data:
            self.post_listbox.insert(tk.END, post["title"])

    def on_post_select(self, event):
        selection_indices = self.post_listbox.curselection()
        if not selection_indices:
            return
        
        index = selection_indices[0]
        post = self.posts_data[index]
        
        self.title_entry.delete(0, tk.END)
        self.title_entry.insert(0, post["title"])
        self.category_entry.delete(0, tk.END)
        self.category_entry.insert(0, post["category"])
        self.pdf_path_var.set("") # Clear PDF path on selection

    def browse_pdf(self):
        filepath = filedialog.askopenfilename(
            title="PDF Dosyası Seç",
            filetypes=(("PDF Files", "*.pdf"), ("All files", "*.*"))
        )
        if filepath:
            self.pdf_path_var.set(filepath)
            
    def create_slug(self, title):
        # Turkish character replacements for URL-friendly slugs
        s = title.lower()
        s = s.replace('ı', 'i').replace('ö', 'o').replace('ü', 'u').replace('ş', 's').replace('ç', 'c').replace('ğ', 'g')
        s = re.sub(r'[^\w\s-]', '', s) # Remove non-alphanumeric
        s = re.sub(r'[\s_-]+', '-', s).strip('-') # Replace spaces/dashes with a single dash
        return s

    def create_new(self):
        title = self.title_entry.get().strip()
        category = self.category_entry.get().strip()
        pdf_path = self.pdf_path_var.get()

        if not all([title, category, pdf_path]):
            messagebox.showerror("Hata", "Lütfen tüm alanları doldurun.")
            return

        slug = self.create_slug(title)
        
        if any(p['slug'] == slug for p in self.posts_data):
            messagebox.showerror("Hata", "Bu başlığa sahip bir makale zaten mevcut.")
            return

        try:
            # Extract text from PDF
            doc = fitz.open(pdf_path)
            content = ""
            for page in doc:
                content += page.get_text()
            doc.close()

            # Create new post data
            new_post = {
                "slug": slug,
                "title": title,
                "date": datetime.datetime.now().strftime("%d %B %Y"), # e.g., 21 June 2025
                "category": category,
                "excerpt": " ".join(content.split()[:30]) + "...", # First 30 words
                "image_url": "https://placehold.co/600x400/1d3557/f8f7f4?text=Makale" # Placeholder
            }
            
            # Create .md file
            with open(os.path.join(REPO_PATH, f"{slug}.md"), "w", encoding="utf-8") as f:
                f.write(content)
                
            self.posts_data.insert(0, new_post) # Add to the top of the list
            self.refresh_listbox()
            self.clear_form()
            messagebox.showinfo("Başarılı", f"'{title}' başlıklı makale oluşturuldu. Değişiklikleri yayınlamayı unutmayın.")
            
        except Exception as e:
            messagebox.showerror("Hata", f"Makale oluşturulurken bir hata oluştu: {e}")

    def update_post(self):
        selection_indices = self.post_listbox.curselection()
        if not selection_indices:
            messagebox.showerror("Hata", "Lütfen güncellemek için bir makale seçin.")
            return
            
        index = selection_indices[0]
        slug = self.posts_data[index]["slug"]
        
        title = self.title_entry.get().strip()
        category = self.category_entry.get().strip()
        pdf_path = self.pdf_path_var.get()
        
        if not all([title, category]):
            messagebox.showerror("Hata", "Başlık ve Kategori alanları boş bırakılamaz.")
            return

        # Update metadata
        self.posts_data[index]["title"] = title
        self.posts_data[index]["category"] = category
        
        # If a new PDF is provided, update content
        if pdf_path:
            try:
                doc = fitz.open(pdf_path)
                content = ""
                for page in doc:
                    content += page.get_text()
                doc.close()
                
                with open(os.path.join(REPO_PATH, f"{slug}.md"), "w", encoding="utf-8") as f:
                    f.write(content)
                
                self.posts_data[index]["excerpt"] = " ".join(content.split()[:30]) + "..."
            except Exception as e:
                messagebox.showerror("Hata", f"PDF okunurken bir hata oluştu: {e}")
                return
        
        self.refresh_listbox()
        self.clear_form()
        messagebox.showinfo("Başarılı", f"'{title}' başlıklı makale güncellendi. Değişiklikleri yayınlamayı unutmayın.")

    def delete_post(self):
        selection_indices = self.post_listbox.curselection()
        if not selection_indices:
            messagebox.showerror("Hata", "Lütfen silmek için bir makale seçin.")
            return
            
        index = selection_indices[0]
        post = self.posts_data[index]
        
        if messagebox.askyesno("Onay", f"'{post['title']}' başlıklı makaleyi silmek istediğinizden emin misiniz?"):
            slug = post["slug"]
            md_path = os.path.join(REPO_PATH, f"{slug}.md")
            
            # Delete md file if it exists
            if os.path.exists(md_path):
                os.remove(md_path)
                
            # Remove from data
            self.posts_data.pop(index)
            self.refresh_listbox()
            self.clear_form()
            messagebox.showinfo("Başarılı", "Makale silindi. Değişiklikleri yayınlamayı unutmayın.")

    def clear_form(self):
        self.title_entry.delete(0, tk.END)
        self.category_entry.delete(0, tk.END)
        self.pdf_path_var.set("")
        self.post_listbox.selection_clear(0, tk.END)

    def publish_changes(self):
        try:
            # Save the index file first
            self.save_posts()

            # Git operations
            self.repo.git.add(A=True) # Stage all changes

            # Check if there are changes to commit
            if not self.repo.is_dirty(untracked_files=True):
                messagebox.showinfo("Bilgi", "Yayınlanacak yeni değişiklik bulunmuyor.")
                return

            commit_message = f"Content update: {datetime.datetime.now().isoformat()}"
            self.repo.index.commit(commit_message)
            
            # Push to remote
            origin = self.repo.remote(name='origin')
            origin.push()
            
            messagebox.showinfo("Başarılı", "Tüm değişiklikler başarıyla yayınlandı!")

        except Exception as e:
            messagebox.showerror("Yayınlama Hatası", f"Değişiklikler yayınlanırken bir hata oluştu:\n\n{e}\n\nLütfen internet bağlantınızı ve Git yapılandırmanızı kontrol edin.")


if __name__ == "__main__":
    app = BlogManager()
    app.mainloop()

