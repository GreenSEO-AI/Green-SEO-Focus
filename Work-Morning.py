import tkinter as tk
from tkinter import ttk, messagebox, font, filedialog
import datetime
import os
import time
import threading
import psutil
import re
import win32gui
import socket
import urllib.request
import json
import win32con
import winreg
import sys
import subprocess
import glob
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import pandas as pd
import seaborn as sns
from datetime import timedelta, datetime, date
import calendar

# Palette de couleurs inspirée de ton site
COLORS = {
    "dark_blue": "#1c2738",  # Bleu foncé (fond principal)
    "medium_blue": "#2c3e50", # Bleu moyen (éléments secondaires)
    "accent_green": "#4ecca3", # Vert d'accent (comme ton logo ECO-TECH)
    "light_blue": "#3498db",  # Bleu clair (boutons, liens)
    "text_light": "#ecf0f1",  # Texte clair
    "text_dark": "#2c3e50",   # Texte foncé
    "warning_red": "#e74c3c"  # Rouge pour alertes
}

class FocusTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("Tracker de Focus Green SEO")
        
        # Fenêtre encore plus grande
        self.root.geometry("650x700")  # Agrandie en hauteur, largeur identique
        
        # Variables
        self.current_task = tk.StringVar()
        self.time_per_task = tk.IntVar(value=30)  # Minutes par défaut
        self.running_task = False
        self.task_start_time = None
        self.completed_tasks = []
        self.banned_sites = ["facebook.com", "twitter.com", "x.com", "youtube.com", "instagram.com"]
        self.enable_blocking = tk.BooleanVar(value=False)  # Par défaut désactivé
        self.block_notifications = tk.BooleanVar(value=False)  # Par défaut désactivé
        self.block_discord = tk.BooleanVar(value=False)  # Nouvelle option pour Discord
        self.last_warning_time = 0  # Pour limiter la fréquence des alertes
        self.last_warned_site = ""  # Pour éviter d'alerter plusieurs fois pour le même site
        self.original_notification_state = None
        
        # UI
        self.create_ui()
        
        # Thread de surveillance
        self.monitoring_active = False
        self.monitoring_thread = None
    
    def create_ui(self):
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(fill="both", expand=True)
        
        # En-tête
        ttk.Label(main_frame, text="Focus Green SEO", font=("Arial", 16, "bold")).pack(pady=(0, 20))
        
        # Entrée de tâche
        task_frame = ttk.Frame(main_frame)
        task_frame.pack(fill="x", pady=10)
        
        ttk.Label(task_frame, text="Tâche:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(task_frame, textvariable=self.current_task, width=40).grid(row=0, column=1, padx=5, pady=5)
        
        # Minuteur
        timer_frame = ttk.Frame(main_frame)
        timer_frame.pack(fill="x", pady=10)
        
        ttk.Label(timer_frame, text="Rappel toutes les (minutes):").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ttk.Spinbox(timer_frame, from_=5, to=60, increment=5, textvariable=self.time_per_task, width=5).grid(row=0, column=1, padx=5, pady=5)
        
        # Option de blocage avec widget canvas custom
        blocking_frame = ttk.Frame(main_frame)
        blocking_frame.pack(fill="x", pady=5)
        
        ttk.Label(blocking_frame, text="Bloquer les distractions:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        # Créer un canvas pour notre propre checkbox
        checkbox_size = 20
        checkbox_canvas = tk.Canvas(blocking_frame, width=checkbox_size, height=checkbox_size, 
                                 bg=COLORS["dark_blue"], highlightthickness=0)
        checkbox_canvas.grid(row=0, column=1, padx=5, pady=5)
        
        # Dessiner notre propre checkbox
        def update_checkbox():
            checkbox_canvas.delete("all")
            checkbox_canvas.create_rectangle(0, 0, checkbox_size, checkbox_size, 
                                         outline=COLORS["light_blue"], width=2)
            if self.enable_blocking.get():
                checkbox_canvas.create_rectangle(4, 4, checkbox_size-4, checkbox_size-4, 
                                             fill=COLORS["accent_green"], outline="")
        
        # Fonction pour toggler le checkbox
        def toggle_checkbox(event):
            self.enable_blocking.set(not self.enable_blocking.get())
            update_checkbox()
        
        # Attacher l'event et dessiner l'état initial
        checkbox_canvas.bind("<Button-1>", toggle_checkbox)
        update_checkbox()
        
        # Après le checkbox de blocage des distractions, ajoute:
        notification_frame = ttk.Frame(main_frame)
        notification_frame.pack(fill="x", pady=5)
        
        ttk.Label(notification_frame, text="Bloquer les notifications:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        # Créer un canvas pour notre propre checkbox de notifications
        notification_canvas = tk.Canvas(notification_frame, width=checkbox_size, height=checkbox_size, 
                                     bg=COLORS["dark_blue"], highlightthickness=0)
        notification_canvas.grid(row=0, column=1, padx=5, pady=5)
        
        # Dessiner notre propre checkbox
        def update_notification_checkbox():
            notification_canvas.delete("all")
            notification_canvas.create_rectangle(0, 0, checkbox_size, checkbox_size, 
                                             outline=COLORS["light_blue"], width=2)
            if self.block_notifications.get():
                notification_canvas.create_rectangle(4, 4, checkbox_size-4, checkbox_size-4, 
                                                 fill=COLORS["accent_green"], outline="")
        
        # Fonction pour toggler le checkbox
        def toggle_notification_checkbox(event):
            self.block_notifications.set(not self.block_notifications.get())
            update_notification_checkbox()
        
        # Attacher l'event et dessiner l'état initial
        notification_canvas.bind("<Button-1>", toggle_notification_checkbox)
        update_notification_checkbox()
        
        # Option Discord spécifique
        discord_frame = ttk.Frame(main_frame)
        discord_frame.pack(fill="x", pady=5)
        
        ttk.Label(discord_frame, text="Configurer Discord:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        # Créer un canvas pour notre propre checkbox de Discord
        discord_canvas = tk.Canvas(discord_frame, width=checkbox_size, height=checkbox_size, 
                                 bg=COLORS["dark_blue"], highlightthickness=0)
        discord_canvas.grid(row=0, column=1, padx=5, pady=5)
        
        # Petit bouton d'aide à côté
        discord_help_button = ttk.Button(discord_frame, text="?", width=2, 
                                       command=lambda: self.show_discord_help())
        discord_help_button.grid(row=0, column=2, padx=2, pady=5)
        
        # Dessiner notre propre checkbox
        def update_discord_checkbox():
            discord_canvas.delete("all")
            discord_canvas.create_rectangle(0, 0, checkbox_size, checkbox_size, 
                                         outline=COLORS["light_blue"], width=2)
            if self.block_discord.get():
                discord_canvas.create_rectangle(4, 4, checkbox_size-4, checkbox_size-4, 
                                             fill=COLORS["accent_green"], outline="")
        
        # Fonction pour toggler le checkbox
        def toggle_discord_checkbox(event):
            self.block_discord.set(not self.block_discord.get())
            update_discord_checkbox()
        
        # Attacher l'event et dessiner l'état initial
        discord_canvas.bind("<Button-1>", toggle_discord_checkbox)
        update_discord_checkbox()
        
        # Barre de progression
        self.progress_var = tk.DoubleVar(value=0.0)
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill="x", pady=10)
        
        ttk.Label(progress_frame, text="Progression:").pack(anchor="w", padx=5)
        self.progress_bar = ttk.Progressbar(progress_frame, 
                                           orient="horizontal", 
                                           length=300, 
                                           mode="determinate",
                                           variable=self.progress_var)
        self.progress_bar.pack(fill="x", padx=5, pady=5)
        
        # Boutons de contrôle
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill="x", pady=20)
        
        self.start_button = ttk.Button(buttons_frame, text="Démarrer la tâche", command=self.start_task)
        self.start_button.pack(side="left", padx=5)
        
        self.complete_button = ttk.Button(buttons_frame, text="Tâche terminée", command=self.complete_task, state="disabled")
        self.complete_button.pack(side="left", padx=5)
        
        self.report_button = ttk.Button(buttons_frame, text="Générer rapport", command=self.generate_report)
        self.report_button.pack(side="right", padx=5)
        
        # Statut
        self.status_label = ttk.Label(main_frame, text="Prêt", font=("Arial", 10, "italic"))
        self.status_label.pack(pady=10)
        
        # Liste des tâches complétées
        ttk.Label(main_frame, text="Tâches complétées:").pack(anchor="w")
        
        self.task_list = tk.Listbox(main_frame, height=8, width=50,
                                  bg=COLORS["medium_blue"], 
                                  fg=COLORS["text_light"],
                                  selectbackground=COLORS["accent_green"],
                                  selectforeground=COLORS["dark_blue"],
                                  font=("Arial", 10))
        self.task_list.pack(fill="both", expand=True, pady=10)
        
        # Ajoute une scrollbar
        task_scroll = ttk.Scrollbar(self.task_list, orient="vertical", 
                                  command=self.task_list.yview)
        self.task_list.configure(yscrollcommand=task_scroll.set)
        task_scroll.pack(side="right", fill="y")
        
        # Export frame
        export_frame = ttk.Frame(main_frame)
        export_frame.pack(fill="x", pady=5)
        
        analytics_button = ttk.Button(export_frame, text="📊 Analytics", command=self.show_analytics_ui)
        analytics_button.pack(side="left", padx=5)
        
        import_button = ttk.Button(export_frame, text="📥 Importer", command=self.import_reports)
        import_button.pack(side="left", padx=5)
        
        export_button = ttk.Button(export_frame, text="📤 Exporter", command=self.show_export_options)
        export_button.pack(side="left", padx=5)
        
        about_button = ttk.Button(export_frame, text="ℹ️ À propos", command=self.show_about)
        about_button.pack(side="right", padx=5)
        
        # Apply theme
        self.apply_theme()
    
    def apply_theme(self):
        # Créer des styles personnalisés
        style = ttk.Style()
        style.theme_use('clam')  # Base theme
        
        # Configure global background
        style.configure("TFrame", background=COLORS["dark_blue"])
        style.configure("TLabel", background=COLORS["dark_blue"], foreground=COLORS["text_light"])
        style.configure("TButton", background=COLORS["light_blue"], foreground=COLORS["text_light"])
        
        # Header style
        self.header_font = font.Font(family="Arial", size=16, weight="bold")
        
        # Button styles
        style.configure("Start.TButton", background=COLORS["accent_green"])
        style.configure("Complete.TButton", background=COLORS["light_blue"])
        style.configure("Report.TButton", background=COLORS["medium_blue"])
        
        # Apply to root window
        self.root.configure(bg=COLORS["dark_blue"])
        
        # Custom Listbox colors
        self.task_list.configure(
            bg=COLORS["medium_blue"], 
            fg=COLORS["text_light"],
            selectbackground=COLORS["accent_green"],
            selectforeground=COLORS["dark_blue"],
            borderwidth=1,
            highlightthickness=1,
            highlightcolor=COLORS["accent_green"],
            highlightbackground=COLORS["light_blue"]
        )
        
        # Style pour les champs de saisie
        style.configure("TEntry", 
                        fieldbackground=COLORS["medium_blue"],
                        foreground=COLORS["text_light"],
                        insertcolor=COLORS["accent_green"],  # Curseur de texte
                        borderwidth=1,
                        relief="solid")
        
        # Style pour les widgets Spinbox
        style.configure("TSpinbox", 
                       fieldbackground=COLORS["medium_blue"],
                       foreground=COLORS["text_light"],
                       arrowcolor=COLORS["accent_green"],
                       borderwidth=1)
        
        # Changer les couleurs de sélection
        self.root.option_add("*TEntry*selectBackground", COLORS["accent_green"])
        self.root.option_add("*TEntry*selectForeground", COLORS["dark_blue"])
        
        # Style pour les checkbuttons
        style.configure("TCheckbutton", 
                       background=COLORS["dark_blue"],
                       foreground=COLORS["text_light"])
        style.map("TCheckbutton",
                 background=[("active", COLORS["medium_blue"])],
                 indicatorcolor=[("selected", COLORS["accent_green"]), 
                                ("!selected", COLORS["light_blue"])])
        
        # Effet de survol pour les boutons
        style.map("TButton",
                 background=[("active", COLORS["accent_green"]), 
                            ("!active", COLORS["light_blue"])],
                 foreground=[("active", COLORS["dark_blue"]), 
                            ("!active", COLORS["text_light"])])
        
        # Ajoute un style personnalisé pour la barre de progression
        style.configure("TProgressbar", 
                       background=COLORS["accent_green"],
                       troughcolor=COLORS["medium_blue"],
                       borderwidth=0,
                       thickness=10)
    
    def add_hover_effects(self):
        # Effet de transition douce pour les boutons
        for button in [self.start_button, self.complete_button, self.report_button]:
            def on_enter(e, btn=button):
                btn.configure(style="Hover.TButton")
            def on_leave(e, btn=button):
                btn.configure(style="TButton")
            button.bind("<Enter>", on_enter)
            button.bind("<Leave>", on_leave)
        
        # Style pour les transitions
        style = ttk.Style()
        style.configure("Hover.TButton", 
                       background=COLORS["accent_green"],
                       foreground=COLORS["dark_blue"])
    
    def start_task(self):
        if not self.current_task.get().strip():
            messagebox.showerror("Erreur", "Veuillez entrer une tâche!")
            return
        
        self.running_task = True
        self.task_start_time = datetime.now()
        
        # Mise à jour UI
        self.start_button.config(state="disabled")
        self.complete_button.config(state="normal")
        self.status_label.config(text=f"Tâche en cours: {self.current_task.get()}")
        
        # Démarrer monitoring si pas déjà actif
        if not self.monitoring_active:
            self.monitoring_active = True
            self.monitoring_thread = threading.Thread(target=self.monitor_distractions, daemon=True)
            self.monitoring_thread.start()
        
        # Programmer le premier rappel
        self.schedule_reminder()
        
        # Mettre à jour cette barre selon le temps écoulé/prévu
        self.update_progress()
        
        # Si le blocage des notifications est activé
        if self.block_notifications.get():
            self.block_specific_notifications(True)
        
        # Si l'option Discord est activée
        if self.block_discord.get():
            self.configure_discord()
    
    def complete_task(self):
        if not self.running_task:
            return
        
        end_time = datetime.now()
        elapsed_time = end_time - self.task_start_time
        hours, remainder = divmod(elapsed_time.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        task_info = {
            "task": self.current_task.get(),
            "start_time": self.task_start_time,
            "end_time": end_time,
            "elapsed": f"{hours}h {minutes}m {seconds}s"
        }
        
        self.completed_tasks.append(task_info)
        
        # Mise à jour UI
        self.task_list.insert(tk.END, f"{self.current_task.get()} - {task_info['elapsed']}")
        self.current_task.set("")
        self.start_button.config(state="normal")
        self.complete_button.config(state="disabled")
        self.status_label.config(text=f"Tâche terminée! Durée: {task_info['elapsed']}")
        
        self.running_task = False
        
        # Annuler les rappels programmés
        for reminder_id in getattr(self, 'reminder_ids', []):
            try:
                self.root.after_cancel(reminder_id)
            except:
                pass
        self.reminder_ids = []
        
        # Restaurer l'état des notifications si elles ont été désactivées
        if self.block_notifications.get():
            self.block_specific_notifications(False)
        
        # Si l'option Discord est activée
        if self.block_discord.get():
            self.configure_discord()
    
    def schedule_reminder(self):
        if not self.running_task:
            return
        
        minutes = self.time_per_task.get()
        reminder_id = self.root.after(minutes * 60 * 1000, self.show_reminder)
        
        if not hasattr(self, 'reminder_ids'):
            self.reminder_ids = []
        self.reminder_ids.append(reminder_id)
    
    def show_reminder(self):
        if not self.running_task:
            return
        
        # Calculer le temps écoulé
        now = datetime.now()
        elapsed = now - self.task_start_time
        hours, remainder = divmod(elapsed.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        # Créer fenêtre de rappel
        reminder = tk.Toplevel(self.root)
        reminder.title("Rappel Maman")
        reminder.geometry("400x300")
        
        frame = ttk.Frame(reminder, padding=20)
        frame.pack(fill="both", expand=True)
        
        ttk.Label(frame, text="💗 Rappel de ta maman 💗", font=("Arial", 14, "bold")).pack(pady=(0, 20))
        
        message = f"Mon petit, tu travailles sur:\n\n{self.current_task.get()}\n\ndepuis {hours}h {minutes}m.\n\nComment avances-tu? Les peluches veulent savoir! 🧸"
        
        ttk.Label(frame, text=message, wraplength=350).pack(pady=10)
        
        buttons_frame = ttk.Frame(frame)
        buttons_frame.pack(pady=20)
        
        ttk.Button(buttons_frame, text="J'avance bien!", 
                  command=lambda: [self.schedule_reminder(), reminder.destroy()]).pack(side="left", padx=5)
        
        ttk.Button(buttons_frame, text="Tâche terminée!", 
                  command=lambda: [self.complete_task(), reminder.destroy()]).pack(side="left", padx=5)
    
    def monitor_distractions(self):
        while self.monitoring_active:
            if self.running_task:
                if self.enable_blocking.get():
                    self.check_browsers()
                
                # Désactiver les notifications Windows si l'option est activée
                if self.block_notifications.get():
                    try:
                        registry_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\PushNotifications"
                        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, registry_path, 0, winreg.KEY_WRITE) as key:
                            winreg.SetValueEx(key, "ToastEnabled", 0, winreg.REG_DWORD, 0)
                    except Exception as e:
                        print(f"Impossible de désactiver les notifications: {e}")
            
            time.sleep(5)  # Vérifier toutes les 5 secondes
    
    def check_browsers(self):
        if not self.enable_blocking.get():
            return
        
        try:
            # Vérifier toutes les fenêtres visibles
            windows = []
            
            def enum_windows_callback(hwnd, windows):
                if win32gui.IsWindowVisible(hwnd):
                    window_text = win32gui.GetWindowText(hwnd)
                    windows.append((hwnd, window_text))
                return True
            
            win32gui.EnumWindows(enum_windows_callback, windows)
            
            for _, title in windows:
                title_lower = title.lower()
                # Mots-clés plus nombreux et plus spécifiques
                for keyword in ["youtube", "facebook", "twitter", "instagram", "tiktok", "reddit", 
                               "fb.com", "youtu.be", "insta", "reels", "shorts", "tweet", 
                               "x.com", "discord", "whatsapp", "messenger", "notification"]:
                    if keyword in title_lower:
                        self.show_distraction_warning(keyword)
                        return
        except Exception as e:
            print(f"Erreur lors de la vérification: {str(e)}")
    
    def show_distraction_warning(self, site):
        # Éviter les alertes trop fréquentes (pas plus d'une alerte toutes les 60 secondes)
        current_time = time.time()
        if current_time - self.last_warning_time < 60 and self.last_warned_site == site:
            return  # Ignorer les alertes répétées trop rapidement pour le même site
        
        self.last_warning_time = current_time
        self.last_warned_site = site
        
        warning = tk.Toplevel(self.root)
        warning.title("⚠️ ALERTE! ⚠️")
        warning.geometry("400x300")
        warning.configure(bg=COLORS["dark_blue"])
        
        # Mettre la fenêtre au premier plan et la garder au-dessus
        warning.attributes('-topmost', True)
        warning.focus_force()  # Focus forcé
        warning.bell()  # Son d'alerte (optionnel)
        
        frame = ttk.Frame(warning, padding=20)
        frame.pack(fill="both", expand=True)
        
        title_font = font.Font(family="Arial", size=16, weight="bold")
        ttk.Label(frame, text="🧸 Les peluches t'ont vu! 🧸", 
                 font=title_font, foreground=COLORS["warning_red"]).pack(pady=(0, 20))
        
        message = f"Mon petit! Je t'ai attrapé sur {site} alors que tu travailles sur:\n\n{self.current_task.get()}\n\nTu m'avais promis de rester concentré!"
        
        ttk.Label(frame, text=message, wraplength=350).pack(pady=10)
        
        # Bouton avec style geek
        btn = ttk.Button(frame, text="Pardon Maman! Je retourne travailler!", 
                  command=warning.destroy, style="Complete.TButton")
        btn.pack(pady=10)
        
        # Auto-fermeture après 10 secondes pour éviter l'accumulation
        warning.after(10000, warning.destroy)
    
    def generate_report(self):
        if not self.completed_tasks and not self.running_task:
            messagebox.showinfo("Rapport", "Aucune tâche à rapporter!")
            return
        
        date_str = datetime.now().strftime("%Y-%m-%d")
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rapports")
        os.makedirs(output_dir, exist_ok=True)
        
        report_file = os.path.join(output_dir, f"rapport_focus_{date_str}.md")
        
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(f"# 💗 Rapport de Focus Green SEO - {date_str}\n\n")
            
            if self.running_task:
                now = datetime.now()
                elapsed = now - self.task_start_time
                hours, remainder = divmod(elapsed.seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                
                f.write(f"## 🔄 Tâche en cours\n")
                f.write(f"- **Tâche**: {self.current_task.get()}\n")
                f.write(f"- **Débutée à**: {self.task_start_time.strftime('%H:%M:%S')}\n")
                f.write(f"- **En cours depuis**: {hours}h {minutes}m {seconds}s\n\n")
            
            if self.completed_tasks:
                f.write(f"## ✅ Tâches terminées\n")
                total_time_seconds = 0
                
                for i, task in enumerate(self.completed_tasks, 1):
                    duration = task["end_time"] - task["start_time"]
                    total_time_seconds += duration.total_seconds()
                    
                    f.write(f"### Tâche {i}: {task['task']}\n")
                    f.write(f"- **Début**: {task['start_time'].strftime('%H:%M:%S')}\n")
                    f.write(f"- **Fin**: {task['end_time'].strftime('%H:%M:%S')}\n")
                    f.write(f"- **Durée**: {task['elapsed']}\n\n")
                
                # Statistiques
                total_hours, remainder = divmod(total_time_seconds, 3600)
                total_minutes, total_seconds = divmod(remainder, 60)
                avg_seconds = total_time_seconds / len(self.completed_tasks)
                avg_hours, remainder = divmod(avg_seconds, 3600)
                avg_minutes, avg_seconds = divmod(remainder, 60)
                
                f.write(f"## 📊 Statistiques\n")
                f.write(f"- **Tâches terminées**: {len(self.completed_tasks)}\n")
                f.write(f"- **Temps total**: {int(total_hours)}h {int(total_minutes)}m {int(total_seconds)}s\n")
                f.write(f"- **Temps moyen par tâche**: {int(avg_hours)}h {int(avg_minutes)}m {int(avg_seconds)}s\n\n")
            
            f.write(f"## 💌 Message pour l'IA\n\n")
            f.write("Chère Assistant(e) IA,\n\n")
            f.write("Voici mon rapport de focus pour aujourd'hui. J'aimerais avoir ton analyse ")
            f.write("et tes encouragements pour continuer mon projet. ")
            f.write("Ce rapport a été généré par mon système de productivité personnel.\n\n")
            f.write("Pour une expérience optimale:\n")
            f.write("- Avec Claude : Partage ce fichier .md directement\n")
            f.write("- Avec Cursor : Ouvre ce fichier et demande une analyse\n") 
            f.write("- Avec ChatGPT/Mistral : Copie le contenu et demande un feedback\n\n")
            f.write("Merci de m'aider à rester motivé(e) et discipliné(e)!\n")
            f.write("Un entrepreneur en herbe 💪\n")
        
        messagebox.showinfo("Rapport généré", f"Rapport enregistré dans:\n{report_file}")
        # Ouvrir automatiquement le rapport
        os.startfile(report_file) if os.name == 'nt' else os.system(f"open {report_file}")

    def update_progress(self):
        if self.running_task:
            now = datetime.now()
            elapsed = (now - self.task_start_time).total_seconds()
            target_time = self.time_per_task.get() * 60  # en secondes
            progress = min(elapsed / target_time, 1.0) * 100
            self.progress_var.set(progress)
            self.root.after(1000, self.update_progress)  # Mise à jour toutes les secondes

    def block_specific_notifications(self, block=True):
        """Solution ULTRA SIMPLE qui bloque TOUTES les notifications Windows y compris Discord"""
        try:
            # Mode Focus Assistant de Windows (bloque TOUT)
            focus_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Focus Assist"
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, focus_path, 0, winreg.KEY_WRITE) as key:
                    # 0=Off, 1=Priorité uniquement, 2=Alarmes uniquement (bloque TOUT sauf alarmes)
                    winreg.SetValueEx(key, "FocusAssistConfiguration", 0, winreg.REG_DWORD, 2 if block else 0)
                
                # Valeur supplémentaire pour être vraiment sûr
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, focus_path, 0, winreg.KEY_WRITE) as key:
                    winreg.SetValueEx(key, "ManualToggleCount", 0, winreg.REG_DWORD, 1 if block else 0)
                
            except:
                # Fallback: désactiver les notifications par l'autre méthode
                registry_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\PushNotifications"
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, registry_path, 0, winreg.KEY_WRITE) as key:
                    winreg.SetValueEx(key, "ToastEnabled", 0, winreg.REG_DWORD, 0 if block else 1)
            
            return True
        except Exception as e:
            print(f"Erreur blocage notifications: {e}")
            return False

    def show_discord_help(self):
        messagebox.showinfo(
            "Configurer Discord",
            "Lorsque cette option est activée et que Discord est détecté,\n"
            "Green SEO Focus t'aidera à configurer Discord pour:\n\n"
            "• Désactiver les notifications TTS\n"
            "• Mettre en sourdine l'application\n"
            "• Désactiver tous les sons de notification\n\n"
            "Ces réglages permettent d'éviter les distractions sonores\n"
            "et visuelles pendant tes sessions de travail."
        )

    def configure_discord(self):
        """Aide l'utilisateur à configurer Discord pour bloquer les notifications"""
        # Vérifier si Discord est en cours d'exécution
        discord_running = False
        for proc in psutil.process_iter(['pid', 'name']):
            if 'discord' in proc.info['name'].lower():
                discord_running = True
                break
        
        if discord_running:
            # Proposer les instructions pour configurer Discord
            messagebox.showinfo(
                "Instructions Discord",
                "Voici comment configurer Discord pour un meilleur focus:\n\n"
                "1. Dans Discord, clique sur l'icône ⚙️ (Paramètres utilisateur)\n"
                "2. Clique sur 'Notifications' dans le menu de gauche\n"
                "3. Désactive:\n"
                "   • 'Notifications TTS' → Choisis 'Jamais'\n"
                "   • Active 'Désactiver tous les sons'\n"
                "   • Active 'Mettre en sourdine'\n\n"
                "Une fois terminé, reviens à Green SEO Focus!"
            )

    def show_analytics_ui(self):
        """Affiche les graphiques dans l'interface utilisateur"""
        # Vérifier qu'il y a des données
        if not self.completed_tasks:
            # Offrir d'importer des données si aucune tâche n'est complétée
            choice = messagebox.askyesno(
                "Aucune donnée disponible", 
                "Aucune tâche complétée n'a été trouvée. Souhaitez-vous importer des rapports existants?",
                icon="question"
            )
            if choice:
                self.import_reports()
            return
        
        # Créer une nouvelle fenêtre pour afficher tous les graphiques
        analytics_window = tk.Toplevel(self.root)
        analytics_window.title("Green SEO Focus - Analytics")
        analytics_window.geometry("800x600")
        analytics_window.configure(bg=COLORS["dark_blue"])
        
        # Frame principal
        main_frame = ttk.Frame(analytics_window, padding=20)
        main_frame.pack(fill="both", expand=True)
        
        # Titre
        ttk.Label(main_frame, text="📊 Analytics Green SEO Focus", font=("Arial", 16, "bold")).pack(pady=(0, 20))
        
        # Générer les graphiques mais sans les fermer
        results = self.generate_analytics()
        if results is None:
            analytics_window.destroy()
            return
        
        # Créer un notebook pour les onglets
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill="both", expand=True, pady=10)
        
        # Frame pour chaque graphique
        daily_frame = ttk.Frame(notebook)
        heatmap_frame = ttk.Frame(notebook)
        tasks_frame = ttk.Frame(notebook)
        short_tasks_frame = ttk.Frame(notebook)
        
        notebook.add(daily_frame, text="Productivité quotidienne")
        notebook.add(heatmap_frame, text="Heatmap")
        notebook.add(tasks_frame, text="Types de tâches")
        notebook.add(short_tasks_frame, text="Tâches courtes")
        
        # Ajouter les graphiques aux frames
        daily_canvas = FigureCanvasTkAgg(results["daily"]["fig"], daily_frame)
        daily_canvas.draw()
        daily_canvas.get_tk_widget().pack(fill="both", expand=True)
        
        heatmap_canvas = FigureCanvasTkAgg(results["heatmap"]["fig"], heatmap_frame)
        heatmap_canvas.draw()
        heatmap_canvas.get_tk_widget().pack(fill="both", expand=True)
        
        tasks_canvas = FigureCanvasTkAgg(results["tasks"]["fig"], tasks_frame)
        tasks_canvas.draw()
        tasks_canvas.get_tk_widget().pack(fill="both", expand=True)
        
        short_tasks_canvas = FigureCanvasTkAgg(results["short_tasks"]["fig"], short_tasks_frame)
        short_tasks_canvas.draw()
        short_tasks_canvas.get_tk_widget().pack(fill="both", expand=True)
        
        # Boutons d'export
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=10)
        
        # Bouton d'export
        export_button = ttk.Button(
            button_frame, text="📤 Exporter les graphiques", 
            command=lambda: self.show_export_options(results)
        )
        export_button.pack(side="left", padx=5)
        
        # Bouton pour ouvrir le rapport
        report_button = ttk.Button(
            button_frame, text="📝 Voir le rapport", 
            command=lambda: os.startfile(results["report_path"]) if os.name == 'nt' 
                            else os.system(f"open {results['report_path']}")
        )
        report_button.pack(side="left", padx=5)
        
        # Bouton fermer
        close_button = ttk.Button(button_frame, text="Fermer", command=analytics_window.destroy)
        close_button.pack(side="right", padx=5)

    def show_export_options(self, results=None):
        """Affiche les options d'exportation"""
        if not results and not self.completed_tasks:
            messagebox.showinfo("Export", "Aucune donnée à exporter!")
            return
        
        # Si results n'est pas fourni, générer les graphiques
        if not results:
            results = self.generate_analytics()
            if results is None:
                return
        
        # Créer une fenêtre d'options d'export
        export_window = tk.Toplevel(self.root)
        export_window.title("Options d'exportation")
        export_window.geometry("400x300")
        export_window.configure(bg=COLORS["dark_blue"])
        
        # Frame principal
        main_frame = ttk.Frame(export_window, padding=20)
        main_frame.pack(fill="both", expand=True)
        
        # Titre
        ttk.Label(main_frame, text="Exporter vers", font=("Arial", 14, "bold")).pack(pady=(0, 20))
        
        # Options d'export
        export_md = ttk.Button(main_frame, text="Fichier Markdown", 
                              command=lambda: os.startfile(results["report_path"]) if os.name == 'nt' 
                                            else os.system(f"open {results['report_path']}"))
        export_md.pack(fill="x", pady=5)
        
        export_notion = ttk.Button(main_frame, text="Format Notion", command=self.export_to_notion)
        export_notion.pack(fill="x", pady=5)
        
        export_trello = ttk.Button(main_frame, text="Format Trello", command=self.export_to_trello)
        export_trello.pack(fill="x", pady=5)
        
        export_folder = ttk.Button(main_frame, text="Ouvrir dossier d'export", 
                                 command=lambda: os.startfile(os.path.dirname(results["report_path"])) if os.name == 'nt' 
                                               else os.system(f"open {os.path.dirname(results['report_path'])}"))
        export_folder.pack(fill="x", pady=5)
        
        # Bouton fermer
        close_button = ttk.Button(main_frame, text="Fermer", command=export_window.destroy)
        close_button.pack(pady=10)

    def import_reports(self):
        """Importe des rapports depuis des fichiers MD"""
        # Ouvrir une boîte de dialogue pour sélectionner les fichiers en utilisant tkinter directement
        from tkinter import filedialog
        file_paths = filedialog.askopenfilenames(
            title="Sélectionner un ou plusieurs rapports",
            filetypes=[("Rapports Markdown", "*.md"), ("Tous les fichiers", "*.*")]
        )
        
        if not file_paths:
            return
        
        # Traiter chaque fichier sélectionné
        imported_tasks = []
        
        for file_path in file_paths:
            tasks_from_file = self.extract_tasks_from_md(file_path)
            if tasks_from_file:
                imported_tasks.extend(tasks_from_file)
        
        if not imported_tasks:
            messagebox.showinfo("Import", "Aucune tâche valide n'a pu être extraite des fichiers sélectionnés.")
            return
        
        # Demander confirmation pour fusionner avec les tâches existantes
        merge = True
        if self.completed_tasks:
            merge = messagebox.askyesno(
                "Fusion des données", 
                f"Voulez-vous fusionner les {len(imported_tasks)} tâches importées avec vos {len(self.completed_tasks)} tâches actuelles?\n\n"
                "Sélectionnez 'Oui' pour fusionner ou 'Non' pour remplacer les tâches actuelles."
            )
        
        # Fusionner ou remplacer
        if merge:
            self.completed_tasks.extend(imported_tasks)
        else:
            self.completed_tasks = imported_tasks
        
        # Mettre à jour la liste des tâches
        self.task_list.delete(0, tk.END)
        for task in self.completed_tasks:
            elapsed = task["end_time"] - task["start_time"]
            hours, remainder = divmod(elapsed.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            elapsed_str = f"{hours}h {minutes}m {seconds}s"
            self.task_list.insert(tk.END, f"{task['task']} - {elapsed_str}")
        
        messagebox.showinfo("Import", f"{len(imported_tasks)} tâches importées avec succès!")
        
        # Afficher les analytics avec les données importées
        self.show_analytics_ui()

    def extract_tasks_from_md(self, file_path):
        """Extrait les tâches d'un fichier markdown de rapport"""
        tasks = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Vérifier si c'est un rapport valide
            if not "# 💗 Rapport de Focus Green SEO" in content:
                return []
            
            # Extraire la date du rapport
            date_match = re.search(r"# 💗 Rapport de Focus Green SEO - (\d{4}-\d{2}-\d{2})", content)
            report_date = date_match.group(1) if date_match else datetime.now().strftime("%Y-%m-%d")
            
            # Extraire les tâches terminées
            task_blocks = re.findall(r"### Tâche \d+: (.+?)\n- \*\*Début\*\*: (.+?)\n- \*\*Fin\*\*: (.+?)\n- \*\*Durée\*\*: (.+?)\n", content)
            
            for task_name, start_time_str, end_time_str, duration in task_blocks:
                try:
                    # Convertir les chaînes de temps en objets datetime
                    report_datetime = datetime.strptime(report_date, "%Y-%m-%d")
                    
                    # Analyser l'heure de début et de fin
                    start_time = datetime.strptime(start_time_str, "%H:%M:%S")
                    start_time = datetime.combine(report_datetime.date(), start_time.time())
                    
                    end_time = datetime.strptime(end_time_str, "%H:%M:%S")
                    end_time = datetime.combine(report_datetime.date(), end_time.time())
                    
                    # Créer l'objet de tâche
                    task_info = {
                        "task": task_name,
                        "start_time": start_time,
                        "end_time": end_time,
                        "elapsed": duration
                    }
                    
                    tasks.append(task_info)
                except Exception as e:
                    print(f"Erreur lors de l'analyse d'une tâche: {e}")
                    continue
            
            return tasks
        except Exception as e:
            print(f"Erreur lors de la lecture du fichier {file_path}: {e}")
            return []

    def show_about(self):
        """Affiche les informations sur l'application et son créateur"""
        about_window = tk.Toplevel(self.root)
        about_window.title("À propos de Green SEO Focus")
        about_window.geometry("700x500")  # Plus haute
        about_window.configure(bg=COLORS["dark_blue"])
        
        frame = ttk.Frame(about_window, padding=20)
        frame.pack(fill="both", expand=True)
        
        # Logo
        logo_label = ttk.Label(frame, text="👁️", font=("Arial", 40))
        logo_label.pack(pady=10)
        
        # Titre
        title_label = ttk.Label(frame, text="Green SEO Focus", font=("Arial", 16, "bold"))
        title_label.pack(pady=5)
        
        # Version
        version_label = ttk.Label(frame, text="Version 1.0.0")
        version_label.pack()
        
        # Description
        desc_text = (
            "Application de productivité et de suivi du temps conçue pour maximiser "
            "la concentration et minimiser les distractions. Idéale pour les étudiants "
            "OpenClassrooms et les professionnels du développement."
        )
        desc_label = ttk.Label(frame, text=desc_text, wraplength=400)
        desc_label.pack(pady=15)
        
        # Fonctionnalités
        features_text = (
            "• Suivi du temps et rappels personnalisés\n"
            "• Blocage des distractions et des notifications\n"
            "• Configuration spéciale pour Discord\n"
            "• Génération de rapports détaillés\n"
            "• Visualisations analytiques avancées\n"
            "• Export vers des outils externes\n"
            "• Import de rapports existants"
        )
        features_label = ttk.Label(frame, text=features_text, justify="left")
        features_label.pack(pady=10, anchor="w")
        
        # Copyright et licence
        copyright_label = ttk.Label(frame, text="© 2025 - Licence MIT")
        copyright_label.pack(pady=10)
        
        # Bouton fermer
        close_button = ttk.Button(frame, text="Fermer", command=about_window.destroy)
        close_button.pack(pady=10)

    def generate_analytics(self):
        """Génère des graphiques d'analyse basés sur les tâches complétées"""
        if not self.completed_tasks:
            messagebox.showinfo("Analytics", "Aucune tâche pour générer des analytics!")
            return None
        
        # Création du répertoire pour les exports
        date_str = datetime.now().strftime("%Y-%m-%d")
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rapports")
        os.makedirs(output_dir, exist_ok=True)
        
        report_file = os.path.join(output_dir, f"rapport_focus_{date_str}.md")
        
        # Appliquer le style seaborn pour des graphiques plus jolis
        sns.set_style("darkgrid")
        plt.rcParams['axes.facecolor'] = '#2c3e50'
        plt.rcParams['figure.facecolor'] = '#1c2738'
        plt.rcParams['text.color'] = '#ecf0f1'
        plt.rcParams['axes.labelcolor'] = '#ecf0f1'
        plt.rcParams['xtick.color'] = '#ecf0f1'
        plt.rcParams['ytick.color'] = '#ecf0f1'
        
        # Augmenter les marges autour des graphiques pour éviter les erreurs tight_layout
        plt.rcParams['figure.constrained_layout.use'] = True  # Utiliser constrained_layout au lieu de tight_layout
        
        results = {}
        results["report_path"] = report_file
        
        # 1. Graphique de productivité par jour
        daily_data = {}
        for task in self.completed_tasks:
            day = task["start_time"].date()
            elapsed = task["end_time"] - task["start_time"]
            daily_data[day] = daily_data.get(day, 0) + elapsed.total_seconds() / 3600  # en heures
        
        # Remplir les jours manquants
        if len(daily_data) > 1:
            all_days = sorted(daily_data.keys())
            min_day, max_day = min(all_days), max(all_days)
            current_day = min_day
            while current_day <= max_day:
                if current_day not in daily_data:
                    daily_data[current_day] = 0
                current_day += timedelta(days=1)
        
        # Créer le graphique avec des marges plus grandes
        daily_fig, daily_ax = plt.subplots(figsize=(10, 6))
        days = sorted(daily_data.keys())
        hours = [daily_data[day] for day in days]
        day_labels = [day.strftime("%d/%m") for day in days]
        
        bars = daily_ax.bar(day_labels, hours, color=COLORS["accent_green"])
        
        # Ajouter les valeurs sur les barres
        for bar, hour in zip(bars, hours):
            height = bar.get_height()
            daily_ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                         f'{hour:.1f}h', ha='center', va='bottom', color=COLORS["text_light"])
        
        daily_ax.set_xlabel('Date')
        daily_ax.set_ylabel('Heures de travail')
        daily_ax.set_title('Productivité quotidienne')
        
        # Ne pas utiliser tight_layout() directement
        # daily_fig.tight_layout()
        
        # Sauvegarder l'image
        daily_img_path = os.path.join(output_dir, f"productivity_daily_{date_str}.png")
        daily_fig.savefig(daily_img_path, dpi=100, bbox_inches='tight')
        
        results["daily"] = {"fig": daily_fig, "path": daily_img_path}
        
        # 2. Heatmap des heures travaillées par jour de semaine / heure
        hour_weekday_data = {}
        for task in self.completed_tasks:
            start_hour = task["start_time"].hour
            weekday = task["start_time"].weekday()
            weekday_name = calendar.day_name[weekday]
            elapsed = task["end_time"] - task["start_time"]
            
            key = (weekday_name, start_hour)
            hour_weekday_data[key] = hour_weekday_data.get(key, 0) + elapsed.total_seconds() / 3600
        
        # Préparer les données pour la heatmap
        weekdays = [calendar.day_name[i] for i in range(7)]
        hours_of_day = list(range(24))
        
        heatmap_data = np.zeros((len(weekdays), len(hours_of_day)))
        for (day, hour), value in hour_weekday_data.items():
            if day in weekdays:
                day_idx = weekdays.index(day)
                heatmap_data[day_idx, hour] = value
        
        # Créer la heatmap avec figure plus grande
        heatmap_fig, heatmap_ax = plt.subplots(figsize=(14, 8))  # Figure plus grande
        sns.heatmap(heatmap_data, annot=True, fmt=".1f", linewidths=.5, ax=heatmap_ax,
                   xticklabels=[f"{h}h" for h in hours_of_day], 
                   yticklabels=weekdays,
                   cmap="YlGnBu", cbar_kws={'label': 'Heures'})
        
        heatmap_ax.set_title('Quand travailles-tu le plus?')
        
        # Sauvegarder l'image
        heatmap_img_path = os.path.join(output_dir, f"productivity_heatmap_{date_str}.png")
        heatmap_fig.savefig(heatmap_img_path, dpi=100, bbox_inches='tight')
        
        results["heatmap"] = {"fig": heatmap_fig, "path": heatmap_img_path}
        
        # 3. Types de tâches (basé sur les premiers mots)
        task_types = {}
        for task in self.completed_tasks:
            task_name = task["task"].strip()
            # Extraire les premiers mots (jusqu'à 3) comme type de tâche
            words = task_name.split()
            task_type = " ".join(words[:min(2, len(words))])
            
            elapsed = task["end_time"] - task["start_time"]
            task_types[task_type] = task_types.get(task_type, 0) + elapsed.total_seconds() / 3600
        
        # Filtrer pour n'afficher que les top types
        top_types = dict(sorted(task_types.items(), key=lambda x: x[1], reverse=True)[:7])
        
        # Créer le graphique en camembert
        tasks_fig, tasks_ax = plt.subplots(figsize=(10, 10))  # Figure plus grande
        wedges, texts, autotexts = tasks_ax.pie(
            top_types.values(), 
            autopct='%1.1f%%',
            textprops={'color': COLORS["text_light"]},
            colors=sns.color_palette("YlGnBu", len(top_types))
        )
        
        tasks_ax.legend(
            wedges, 
            [f"{k} ({v:.1f}h)" for k, v in top_types.items()],
            loc="center left",
            bbox_to_anchor=(1, 0, 0.5, 1),
            frameon=False
        )
        
        tasks_ax.set_title('Répartition des types de tâches')
        
        # Sauvegarder l'image
        tasks_img_path = os.path.join(output_dir, f"productivity_tasks_{date_str}.png")
        tasks_fig.savefig(tasks_img_path, dpi=100, bbox_inches='tight')
        
        results["tasks"] = {"fig": tasks_fig, "path": tasks_img_path}
        
        # 4. Tâches les plus courtes
        task_durations = []
        for task in self.completed_tasks:
            elapsed = task["end_time"] - task["start_time"]
            duration_min = elapsed.total_seconds() / 60  # en minutes
            task_durations.append((task["task"], duration_min))
        
        # Trier et prendre les 5 plus courtes
        sorted_durations = sorted(task_durations, key=lambda x: x[1])
        shortest = sorted_durations[:5]
        
        # Préparer les données
        short_names = [t[0][:20] + "..." if len(t[0]) > 20 else t[0] for t in shortest]
        short_durations = [t[1] for t in shortest]
        
        # Créer le graphique des tâches courtes avec figure plus grande
        short_fig, short_ax = plt.subplots(figsize=(12, 8))  # Figure plus grande
        bars = short_ax.barh(short_names, short_durations, color=COLORS["light_blue"])
        
        # Ajouter les valeurs sur les barres
        for bar, duration in zip(bars, short_durations):
            width = bar.get_width()
            short_ax.text(width + 1, bar.get_y() + bar.get_height()/2.,
                         f'{duration:.1f} min', ha='left', va='center', color=COLORS["text_light"])
        
        short_ax.set_xlabel('Durée (minutes)')
        short_ax.set_title('Tâches les plus courtes')
        short_ax.invert_yaxis()  # Pour que la plus courte soit en haut
        
        # Sauvegarder l'image
        short_img_path = os.path.join(output_dir, f"productivity_shortest_{date_str}.png")
        short_fig.savefig(short_img_path, dpi=100, bbox_inches='tight')
        
        results["short_tasks"] = {"fig": short_fig, "path": short_img_path}
        
        # Ajouter les images au rapport markdown
        with open(report_file, "a", encoding="utf-8") as f:
            f.write("\n\n## 📊 Visualisations\n\n")
            f.write("### Productivité quotidienne\n\n")
            f.write(f"![Productivité quotidienne](./rapports/productivity_daily_{date_str}.png)\n\n")
            f.write("### Quand travailles-tu le plus?\n\n")
            f.write(f"![Heatmap de productivité](./rapports/productivity_heatmap_{date_str}.png)\n\n")
            f.write("### Types de tâches\n\n")
            f.write(f"![Types de tâches](./rapports/productivity_tasks_{date_str}.png)\n\n")
            f.write("### Tâches les plus courtes\n\n")
            f.write(f"![Tâches les plus courtes](./rapports/productivity_shortest_{date_str}.png)\n\n")
            
            f.write("## 🔄 Comment utiliser ces visualisations\n\n")
            f.write("Ces graphiques peuvent être importés dans:\n\n")
            f.write("- **Notion**: Ajoutez les images à vos tableaux de bord\n")
            f.write("- **Trello**: Joignez-les à vos cartes de suivi\n")
            f.write("- **GitHub**: Intégrez-les à vos README pour suivre l'avancement\n")
            f.write("- **Présentations**: Parfait pour les revues de projet\n\n")
        
        return results

    def export_to_notion(self):
        """Prépare un export optimisé pour Notion"""
        # Vérifier qu'il y a des données
        if not self.completed_tasks:
            messagebox.showinfo("Export Notion", "Aucune tâche à exporter!")
            return
        
        # Générer les analyses si ce n'est pas déjà fait
        results = self.generate_analytics()
        if results is None:
            return
        
        # Créer un fichier d'export spécifique pour Notion
        date_str = datetime.now().strftime("%Y-%m-%d")
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rapports")
        
        notion_file = os.path.join(output_dir, f"notion_export_{date_str}.md")
        
        with open(notion_file, "w", encoding="utf-8") as f:
            f.write(f"# 📊 Rapport Green SEO Focus - {date_str}\n\n")
            
            # Introduction
            f.write("## 🔍 Résumé de productivité\n\n")
            
            # Statistiques
            total_time_seconds = sum((task["end_time"] - task["start_time"]).total_seconds() for task in self.completed_tasks)
            total_hours, remainder = divmod(total_time_seconds, 3600)
            total_minutes, _ = divmod(remainder, 60)
            
            f.write(f"- **Tâches terminées**: {len(self.completed_tasks)}\n")
            f.write(f"- **Temps total**: {int(total_hours)}h {int(total_minutes)}m\n")
            
            if len(self.completed_tasks) > 0:
                avg_seconds = total_time_seconds / len(self.completed_tasks)
                avg_hours, remainder = divmod(avg_seconds, 3600)
                avg_minutes, _ = divmod(remainder, 60)
                f.write(f"- **Temps moyen par tâche**: {int(avg_hours)}h {int(avg_minutes)}m\n\n")
            
            f.write("## 📈 Visualisations\n\n")
            f.write("*Note: Téléchargez les images ci-dessous et importez-les dans votre base Notion*\n\n")
            
            for viz_type in ["daily", "heatmap", "tasks", "short_tasks"]:
                if viz_type in results:
                    img_path = results[viz_type]["path"]
                    img_name = os.path.basename(img_path)
                    f.write(f"### {os.path.splitext(img_name)[0]}\n")
                    f.write(f"![{viz_type}]({img_path})\n\n")
            
            f.write("## ✅ Tâches complétées\n\n")
            
            # Utiliser le format Notion pour les cases à cocher
            for i, task in enumerate(self.completed_tasks, 1):
                task_name = task["task"]
                elapsed = task["elapsed"]
                f.write(f"- [x] **Tâche {i}**: {task_name} ({elapsed})\n")
        
        messagebox.showinfo("Export Notion", f"Export Notion créé:\n{notion_file}\n\nLes images sont dans le dossier 'rapports'")
        os.startfile(notion_file) if os.name == 'nt' else os.system(f"open {notion_file}")

    def export_to_trello(self):
        """Prépare un export optimisé pour Trello"""
        # Vérifier qu'il y a des données
        if not self.completed_tasks:
            messagebox.showinfo("Export Trello", "Aucune tâche à exporter!")
            return
        
        # Générer les analyses si ce n'est pas déjà fait
        results = self.generate_analytics()
        if results is None:
            return
        
        # Créer un fichier d'export spécifique pour Trello
        date_str = datetime.now().strftime("%Y-%m-%d")
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rapports")
        
        trello_file = os.path.join(output_dir, f"trello_export_{date_str}.md")
        
        with open(trello_file, "w", encoding="utf-8") as f:
            f.write(f"# Rapport Green SEO Focus - {date_str}\n\n")
            
            # Résumé simple pour Trello
            f.write("## Résumé\n\n")
            
            # Statistiques
            total_time_seconds = sum((task["end_time"] - task["start_time"]).total_seconds() for task in self.completed_tasks)
            total_hours, remainder = divmod(total_time_seconds, 3600)
            total_minutes, _ = divmod(remainder, 60)
            
            f.write(f"- **Tâches terminées**: {len(self.completed_tasks)}\n")
            f.write(f"- **Temps total**: {int(total_hours)}h {int(total_minutes)}m\n\n")
            
            f.write("## Instructions\n\n")
            f.write("1. Créez une carte 'Rapport de productivité' dans votre tableau Trello\n")
            f.write("2. Copiez ce contenu dans la description de la carte\n")
            f.write("3. Téléchargez les images du dossier 'rapports' et ajoutez-les comme pièces jointes\n\n")
            
            f.write("## Tâches complétées\n\n")
            
            # Format de liste pour Trello
            for i, task in enumerate(self.completed_tasks, 1):
                task_name = task["task"]
                elapsed = task["elapsed"]
                start_time = task["start_time"].strftime("%H:%M")
                end_time = task["end_time"].strftime("%H:%M")
                f.write(f"- {task_name} ({start_time} - {end_time}, durée: {elapsed})\n")
        
        messagebox.showinfo("Export Trello", f"Export Trello créé:\n{trello_file}\n\nLes images sont dans le dossier 'rapports'")
        os.startfile(trello_file) if os.name == 'nt' else os.system(f"open {trello_file}")

if __name__ == "__main__":
    root = tk.Tk()
    
    # Solution robuste pour trouver l'image peu importe le contexte (dev ou exe)
    try:
        # Méthode améliorée pour Windows
        if getattr(sys, 'frozen', False):
            # En mode exe
            base_dir = sys._MEIPASS
            ico_path = os.path.join(base_dir, "favicon.ico")
            # Définir l'icône à la fois pour la fenêtre et la barre des tâches
            root.iconbitmap(default=ico_path)
            root.wm_iconbitmap(ico_path)
        else:
            # En développement - charge directement l'image originale
            root.iconbitmap("favicon.ico")
            root.wm_iconbitmap("favicon.ico")
    except Exception as e:
        print(f"Erreur icône: {e}")
        # Plan B si ico échoue
        try:
            icon = tk.PhotoImage(file="android-chrome-512x512.png")
            root.iconphoto(True, icon)
        except:
            pass
    
    app = FocusTracker(root)
    root.mainloop()