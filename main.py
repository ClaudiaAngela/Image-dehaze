import tkinter as tk  #Interfata grafica (Tkinter)
from tkinter import ttk, filedialog, messagebox

import matplotlib
matplotlib.use("TkAgg")  # backend pentru integrarea Matplotlib in Tkinter
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

# importam functiile de prelucrare si de afisare din modulul de algoritm
from dehaze_morphology import (
    dehaze_with_morphology,
    plot_morph_ops,
    plot_gray_hist,
    plot_dehaze_results,
)


# Clasa principala a aplicatiei ( creaza fereastra Tkinter, construirea layout-ului, citirea parametrilor din interfata, apelearea functiilor din dehaze_morphology)
class DehazeGUI:

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Eliminarea ceții din imagini")
        self.root.geometry("1200x720")
        self.root.minsize(1000, 650)


        self.root.configure(bg="#181a24")   #coloare de fundal pentru fereastra

        # calea imaginii selectate din calculator
        self.img_path = None
        # dictionar in care memoram rezultatele ultimei procesari
        self.results = None

        # definim stilurile grafice pentru widget-urile ttk
        self._setup_style()
        # construim structura vizuala (panou stanga + panou dreapta)
        self._build_layout()

    #  configurare stil ttk
    def _setup_style(self):
        self.root.option_add("*Font", "Calibri")

        style = ttk.Style()
        # folosim tema "clam", care e eficienta pe mai multe sisteme
        try:
            style.theme_use("clam")
        except tk.TclError:
            # daca tema nu exista, continuam cu tema implicita
            pass

        # culorile de baza folosite in interfata
        primary = "#ff8a3d"      # pentru butoanele principale
        primary_dark = "#e37227"
        secondary = "#3a7bd5"    # pentru butoanele secundare
        secondary_dark = "#2c5fa7"
        card_bg = "#232538"      # pentru panoul din stanga
        light_text = "#f4f4f7"
        muted_text = "#c0c3d7"

        # stil pentru frame-ul din stanga
        style.configure(
            "Left.TFrame",
            background=card_bg,
            relief="flat",
        )
        # stil pentru frame-ul din dreapta
        style.configure(
            "Right.TFrame",
            background="#181a24",
            relief="flat",
        )

        # stil pentru diferite tipuri de label-uri
        style.configure(
            "Title.TLabel",
            background=card_bg,
            foreground=light_text,
            font=("Segoe UI", 12, "bold"),
        )
        style.configure(
            "Section.TLabel",
            background=card_bg,
            foreground=light_text,
            font=("Segoe UI", 10, "bold"),
        )
        style.configure(
            "Text.TLabel",
            background=card_bg,
            foreground=muted_text,
            font=("Segoe UI", 9),
        )

        # stil pentru butoanele principale (Alege imagine / Proceseaza)
        style.configure(
            "Primary.TButton",
            font=("Segoe UI", 10, "bold"),
            background=primary,
            foreground="white",
            borderwidth=0,
            padding=(8, 5),
        )
        style.map(
            "Primary.TButton",
            background=[("pressed", primary_dark), ("active", primary_dark)],
            foreground=[("disabled", "#888888")],
        )

        # stil pentru butoanele secundare (Figura 1 / Figura 2 / Figura 3)
        style.configure(
            "Secondary.TButton",
            font=("Segoe UI", 9, "bold"),
            background=secondary,
            foreground="white",
            borderwidth=0,
            padding=(6, 4),
        )
        style.map(
            "Secondary.TButton",
            background=[("pressed", secondary_dark), ("active", secondary_dark)],
            foreground=[("disabled", "#bbbbbb")],
        )

        # stiluri pentru slider, spinbox si entry (campuri de input numeric)
        style.configure(
            "TScale",
            background=card_bg,
        )
        style.configure(
            "TSpinbox",
            fieldbackground="#181a24",
            foreground=light_text,
            bordercolor="#3a3c4f",
            arrowsize=12,
        )
        style.configure(
            "TEntry",
            fieldbackground="#181a24",
            foreground=light_text,
            bordercolor="#3a3c4f",
        )

    #  layout principal
    # Creeaza containerul principal si imparte fereastra in cele 2 coloane (stanga si dreapta)
    def _build_layout(self):

        container = ttk.Frame(self.root, style="Right.TFrame")
        container.pack(fill=tk.BOTH, expand=True)

        container.columnconfigure(1, weight=1)
        container.rowconfigure(0, weight=1)

        # in stanga avem un wrapper pentru card-ul cu parametri
        left_wrapper = ttk.Frame(container, style="Right.TFrame")
        left_wrapper.grid(row=0, column=0, sticky="nsw", padx=(20, 10), pady=20)

        # card-ul efectiv in care punem controalele
        left_frame = ttk.Frame(left_wrapper, style="Left.TFrame", padding=15)
        left_frame.pack(fill=tk.Y, expand=False)

        # in dreapta avem zona in care se deseneaza imaginile Matplotlib
        right_frame = ttk.Frame(container, style="Right.TFrame", padding=10)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(0, 20), pady=20)

        self._build_left_panel(left_frame)
        self._build_right_panel(right_frame)

    # =====================   panou UI stanga
    # Construirea panoului din stanga: buton pentru alegerea imaginii, controale pentru parametrii si butoane pentru figurile 1/2/3
    def _build_left_panel(self, frame: ttk.Frame):

        ttk.Label(
            frame, text="Parametri algoritmului", style="Title.TLabel"
        ).pack(anchor=tk.W, pady=(0, 8))

        # buton pentru selectarea imaginii de pe disc
        btn_choose = ttk.Button(
            frame,
            text=" Alege imagine...",
            style="Primary.TButton",
            command=self.choose_image,
        )
        btn_choose.pack(fill=tk.X, pady=(0, 12))

        # separator pentru a delimita zona de parametri
        ttk.Separator(frame).pack(fill=tk.X, pady=(5, 10))

        # slider pentru transmisie minima
        ttk.Label(frame, text="t_min (transmisie minimă):", style="Section.TLabel").pack(
            anchor=tk.W
        )
        self.tmin_var = tk.DoubleVar(value=0.85)
        scl_tmin = ttk.Scale(
            frame,
            from_=0.5,
            to=0.98,
            orient=tk.HORIZONTAL,
            variable=self.tmin_var,
            command=self._update_tmin_label,
        )
        scl_tmin.pack(fill=tk.X, pady=(0, 2))
        # afisam numeric valoarea curenta a lui t_min
        self.lbl_tmin_val = ttk.Label(frame, text="0.85", style="Text.TLabel")
        self.lbl_tmin_val.pack(anchor=tk.E, pady=(0, 8))

        # câmp pentru dimensiunea kernel-ului morfologic
        ttk.Label(
            frame, text="Dimensiune kernel (pixeli, impar):", style="Section.TLabel"
        ).pack(anchor=tk.W)
        self.kernel_var = tk.IntVar(value=15)
        spn_kernel = ttk.Spinbox(
            frame,
            from_=3,
            to=51,
            increment=2,
            textvariable=self.kernel_var,
            width=6,
            justify="center",
        )
        spn_kernel.pack(fill=tk.X, pady=(0, 8))

        # camp pentru parametrul omega
        ttk.Label(frame, text="Omega (0.7 – 0.98):", style="Section.TLabel").pack(
            anchor=tk.W
        )
        self.omega_var = tk.DoubleVar(value=0.95)
        ent_omega = ttk.Entry(frame, textvariable=self.omega_var, justify="center")
        ent_omega.pack(fill=tk.X, pady=(0, 12))

        # butonul care lanseaza procesarea imaginii selectate
        btn_process = ttk.Button(
            frame,
            text="▶ Proceseaza imaginea",
            style="Primary.TButton",
            command=self.process_image,
        )
        btn_process.pack(fill=tk.X, pady=(0, 10))

        ttk.Separator(frame).pack(fill=tk.X, pady=(10, 10))

        # sectiunea cu butoane pentru figurile detaliate
        ttk.Label(
            frame, text="Vizualizari detaliate", style="Section.TLabel"
        ).pack(anchor=tk.W, pady=(0, 5))

        # buton pentru Figura 1 – operatii morfologice
        self.btn_fig1 = ttk.Button(
            frame,
            text="Figura 1: Operatii morfologice",
            style="Secondary.TButton",
            command=self.show_morph_ops,
            state="disabled",  # activat doar dupa ce procesam o imagine
        )
        self.btn_fig1.pack(fill=tk.X, pady=2)

        # buton pentru Figura 2 – histograma imaginii gri
        self.btn_fig2 = ttk.Button(
            frame,
            text="Figura 2: Histograma imaginii gri",
            style="Secondary.TButton",
            command=self.show_gray_hist,
            state="disabled",
        )
        self.btn_fig2.pack(fill=tk.X, pady=2)

        # buton pentru Figura 3 – rezultatele dehazing complete
        self.btn_fig3 = ttk.Button(
            frame,
            text="Figura 3: Rezultate dehazing complete",
            style="Secondary.TButton",
            command=self.show_dehaze_plots,
            state="disabled",
        )
        self.btn_fig3.pack(fill=tk.X, pady=2)

        ttk.Separator(frame).pack(fill=tk.X, pady=(10, 8))

        # text explicativ pentru parametri
        txt_info = (
            "Explicatii:\n"
            " • t_min crește  → imagine mai luminoasa,\n"
            " • kernel crește → efect morfologic mai puternic\n"
            "             (netezire / uniformizare).\n"
            " • omega crește → scoate mai mult ceata si creste\n"
            "             contrastul global.\n\n"
            "După procesare poți deschide figurile detaliate\n"
            " 1, 2 si 3 din butoanele de mai sus."
        )
        ttk.Label(frame, text=txt_info, style="Text.TLabel", wraplength=260,
                  justify=tk.LEFT).pack(pady=(0, 0))

    # ===============  panou UI dreapta
    # Afisarea imginii originale si a imaginii finale restaurate
    def _build_right_panel(self, frame: ttk.Frame):

        ttk.Label(
            frame,
            text="Comparație imagine originală vs. imagine restaurată",
            foreground="#f4f4f7",
            background="#181a24",
            font=("Segoe UI", 11, "bold"),
        ).pack(anchor=tk.W, pady=(0, 5))

        # cream o figura Matplotlib cu 2 subplots
        self.fig = Figure(figsize=(7.5, 4.8))
        self.ax_orig = self.fig.add_subplot(1, 2, 1)
        self.ax_rest = self.fig.add_subplot(1, 2, 2)

        self.ax_orig.set_title("Imagine originala")
        self.ax_orig.axis("off")
        self.ax_rest.set_title("Imagine restaurata")
        self.ax_rest.axis("off")

        # atasam figura la un widget Tkinter prin FigureCanvasTkAgg
        canvas = FigureCanvasTkAgg(self.fig, master=frame)
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        self.canvas = canvas

    #  functii utilitare
    def _update_tmin_label(self, _event=None):
        """Actualizeaza label-ul numeric pentru t_min cand miscam slider-ul."""
        self.lbl_tmin_val.config(text=f"{self.tmin_var.get():.2f}")


    def choose_image(self):
        # Deschide un dialog de tip Open File pentru a selecta imaginea cu ceata.
        filetypes = [
            ("Imagini", "*.jpg *.jpeg *.png *.bmp *.tif *.tiff"),
            ("Toate fisierele", "*.*"),
        ]
        path = filedialog.askopenfilename(
            title="Selecteaza o imagine cu ceata",
            filetypes=filetypes,
        )
        if path:
            self.img_path = path
            messagebox.showinfo("Imagine selectata", f"Ai ales:\n{path}")

    #  logica de procesare
    def process_image(self):

        # Citeste parametrii din interfata, apeleaza algoritmul de dehazing
        # si actualizeaza afisarea (plus butoanele pentru figuri).

        if not self.img_path:
            messagebox.showwarning("Atentie", "Mai intai alege o imagine.")
            return

        try:
            # citim parametrii din interfata
            t_min = float(self.tmin_var.get())
            omega = float(self.omega_var.get())
            kernel_size = int(self.kernel_var.get())

            # ne asiguram ca kernel-ul este impar
            if kernel_size % 2 == 0:
                kernel_size += 1
                self.kernel_var.set(kernel_size)

            # apelam algoritmul de dehazing din modulul dehaze_morphology
            ImgRGB, ImgGray, dark_channel, t1, t_refined, J_restored_rgb = dehaze_with_morphology(
                self.img_path,
                kernel_size=kernel_size,
                omega=omega,
                t_min=t_min,
            )

            # salvam rezultatele intr-un dictionar pentru a le putea folosi ulterior
            self.results = {
                "ImgRGB": ImgRGB,
                "ImgGray": ImgGray,
                "dark_channel": dark_channel,
                "t1": t1,
                "t_refined": t_refined,
                "J_restored_rgb": J_restored_rgb,
                "kernel_size": kernel_size,
                "t_min": t_min,
            }

            # activam butoanele pentru figurile 1, 2 si 3
            self.btn_fig1.config(state="normal")
            self.btn_fig2.config(state="normal")
            self.btn_fig3.config(state="normal")

            # actualizam subplots-urile din dreapta cu imaginile curente
            self.ax_orig.clear()
            self.ax_rest.clear()

            self.ax_orig.imshow(ImgRGB)
            self.ax_orig.set_title("Imagine originala")
            self.ax_orig.axis("off")

            self.ax_rest.imshow(J_restored_rgb)
            self.ax_rest.set_title("Imagine restaurata (fara ceata)")
            self.ax_rest.axis("off")

            self.canvas.draw()

        except Exception as e:
            # daca ceva nu merge, afisam eroarea intr-un messagebox
            messagebox.showerror("Eroare la procesare", str(e))

    #  actiunile butoanelor pentru figuri
    def show_morph_ops(self):
        #Deschide Figura 1 – operatii morfologice de baza pe imaginea gri
        if not self.results:
            messagebox.showinfo("Info", "Proceseaza mai intai o imagine.")
            return
        plot_morph_ops(self.results["ImgGray"], self.results["kernel_size"])

    def show_gray_hist(self):
        # Deschide Figura 2 – imagine gri + histograma ei.
        if not self.results:
            messagebox.showinfo("Info", "Proceseaza mai intai o imagine.")
            return
        plot_gray_hist(self.results["ImgGray"])

    def show_dehaze_plots(self):
        #Deschide Figura 3 – rezultatele intermediare ale algoritmului de dehazing.
        if not self.results:
            messagebox.showinfo("Info", "Proceseaza mai intai o imagine.")
            return
        r = self.results
        plot_dehaze_results(
            r["ImgRGB"],
            r["dark_channel"],
            r["t1"],
            r["t_refined"],
            r["J_restored_rgb"],
            r["t_min"],
        )


if __name__ == "__main__":
    # punctul de intrare in aplicatie: cream fereastra principala si lansam bucla Tkinter
    root = tk.Tk()
    app = DehazeGUI(root)
    root.mainloop()
