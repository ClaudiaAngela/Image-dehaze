#  Implementarea algoritmului de dehazing si functiile de afisare

import cv2
import numpy as np
import matplotlib.pyplot as plt


def dehaze_with_morphology(img_path, kernel_size=15, omega=0.95, t_min=0.85):
    """
    Aplica algoritmul de dehazing pe o imagine.

    Parametri:
        img_path   : calea catre imagine (string)
        kernel_size: dimensiunea elementului structurant (impar)
        omega      : parametru (0-1) care controleaza cat de agresiv se scoate ceata
        t_min      : transmisia minima (0-1), previne intunecarea excesiva

    Returneaza:
        ImgRGB         - imaginea originala, in format RGB
        ImgGray        - imaginea originala, in tonuri de gri
        dark_channel   - canalul intunecat (Dark Channel Prior)
        t1             - harta de transmisie initiala
        t_refined      - harta de transmisie rafinata morfologic
        J_restored_rgb - imaginea restaurata, fara ceata (RGB)
    """

    # 1. Citirea imaginii de pe disc (OpenCV o incarca in BGR)
    ImgIn = cv2.imread(img_path)
    if ImgIn is None:
        raise FileNotFoundError(f"Imaginea nu a fost gasita la calea: {img_path}")

    # 2. Conversii de baza
    ImgRGB = cv2.cvtColor(ImgIn, cv2.COLOR_BGR2RGB)      # pentru afisare corecta
    ImgGray = cv2.cvtColor(ImgIn, cv2.COLOR_BGR2GRAY)    # imagine pe un singur canal
    ImgFloat = ImgIn.astype(np.float64) / 255.0          # 0–255 -> 0–1 (double)

    # 3. Elementul structurant folosit in operatiile morfologice
    kernel_morph = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (kernel_size, kernel_size)
    )

    # Pasul 1 – Canalul intunecat (Dark Channel Prior - DCP)
    # luam minimul pe cele 3 canale pentru fiecare pixel
    min_channel = np.min(ImgFloat, axis=2)
    # aplicam o eroziune (minim local intr-o fereastra kernel_size x kernel_size)
    dark_channel = cv2.erode(min_channel, kernel_morph)

    # Pasul 2 – Estimarea luminii atmosferice A
    num_pixels = dark_channel.size
    # consideram cei mai luminosi 0.1% pixeli din canalul intunecat
    num_brightest = int(max(num_pixels * 0.001, 1))

    flat_dc = dark_channel.ravel()
    # sortam valorile si luam indicii celor mai mari valori
    indices = np.argsort(flat_dc)[-num_brightest:]

    flat_img = ImgFloat.reshape(-1, 3)
    candidate_pixels = flat_img[indices]

    # calculam luminozitatea fiecarui pixel candidat (B+G+R)
    brightness = np.sum(candidate_pixels, axis=1)
    brightest_pixel_index = np.argmax(brightness)
    # alegem pixelul cu luminozitate maxima ca estimare pentru A
    A = candidate_pixels[brightest_pixel_index]

    # Pasul 3 – Transmisia initiala t1
    # normalizam imaginea prin A (pe fiecare canal)
    normalized_img = ImgFloat / A
    # luam minimul pe canale din imaginea normalizata
    min_channel_normalized = np.min(normalized_img, axis=2)
    # aplicam din nou eroziune pentru a obtine minimul local
    I_min = cv2.erode(min_channel_normalized, kernel_morph)
    # transmisia initiala conform formulei din articol
    t1 = 1.0 - (omega * I_min)

    # Pasul 4 – Rafinarea transmisiei (morfologic)
    # Closing: umple gauri mici intunecate din harta de transmisie
    t2 = cv2.morphologyEx(t1, cv2.MORPH_CLOSE, kernel_morph)
    # Opening: elimina pete albe izolate
    t_refined = cv2.morphologyEx(t2, cv2.MORPH_OPEN, kernel_morph)
    # impunem un prag minim pentru a evita valori prea mici (care ar intuneca imaginea)
    t_refined = np.maximum(t_refined, t_min)

    # Pasul 5 – Restaurarea imaginii J
    # extindem harta de transmisie de la 1 canal la 3 canale
    transmission_map_3d = np.stack([t_refined] * 3, axis=-1)
    # aplicam formula inversa a modelului de ceata
    J = (ImgFloat - A) / transmission_map_3d + A

    # convertim inapoi la intervalul 0–255 si la tip uint8
    J_restored = np.clip(J * 255, 0, 255).astype(np.uint8)
    # convertim BGR -> RGB pentru afisare
    J_restored_rgb = cv2.cvtColor(J_restored, cv2.COLOR_BGR2RGB)

    return ImgRGB, ImgGray, dark_channel, t1, t_refined, J_restored_rgb


# Functii de vizualizare (folosite de GUI)

def plot_morph_ops(ImgGray, kernel_size):
    """
    Figura 1 – operatii morfologice de baza:
      - eroziune
      - dilatare
      - opening
      - closing
    aplicate imaginii in tonuri de gri.
    """
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_size, kernel_size))

    ImgErosion = cv2.erode(ImgGray, kernel)
    ImgDilation = cv2.dilate(ImgGray, kernel)
    ImgOpening = cv2.morphologyEx(ImgGray, cv2.MORPH_OPEN, kernel)
    ImgClosing = cv2.morphologyEx(ImgGray, cv2.MORPH_CLOSE, kernel)

    titles = ['Original', 'Eroziune', 'Dilatare', 'Opening', 'Closing']
    images = [ImgGray, ImgErosion, ImgDilation, ImgOpening, ImgClosing]

    fig, axes = plt.subplots(1, 5, figsize=(15, 4))
    for i in range(5):
        axes[i].imshow(images[i], cmap='gray')
        axes[i].set_title(titles[i])
        axes[i].axis('off')
    fig.suptitle('Figura 1 – Operatii morfologice de baza aplicate imaginii cu ceata',
                 fontsize=12)
    plt.show()


def plot_gray_hist(ImgGray):
    """
    Figura 2 – afiseaza imaginea in tonuri de gri si histograma
    distributiei nivelurilor de gri.
    """
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))

    axes[0].imshow(ImgGray, cmap='gray', vmin=0, vmax=255)
    axes[0].axis('off')
    axes[0].set_title('Imagine initiala (gri)')

    axes[1].hist(ImgGray.ravel(), 256, range=[0, 255], density=True)
    axes[1].set_title('Histograma nivelelor de gri - imagine originală')

    fig.suptitle('Figura 2 – Imagine gri și histograma corespunzatoare', fontsize=12)
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.show()


def plot_dehaze_results(ImgRGB, dark_channel, t1, t_refined, J_restored_rgb, t_min):
    """
    Figura 3 – afiseaza pe aceeasi figura:
      - imaginea originala
      - canalul intunecat (DCP)
      - transmisia initiala
      - transmisia rafinata
      - imaginea restaurata
      - histograma imaginii restaurate
    """
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    fig.suptitle('Figura 3 – Rezultatele implementării intermediare (Dehazing)',
                 fontsize=16)

    axes[0, 0].imshow(ImgRGB)
    axes[0, 0].set_title('Imagine originala (I)')
    axes[0, 0].axis('off')

    axes[0, 1].imshow(dark_channel, cmap='gray')
    axes[0, 1].set_title('Canalul intunecat (DCP)')
    axes[0, 1].axis('off')

    axes[0, 2].imshow(t1, cmap='gray', vmin=0, vmax=1)
    axes[0, 2].set_title('Transmisia initiala (t1)')
    axes[0, 2].axis('off')

    axes[1, 0].imshow(t_refined, cmap='gray', vmin=0, vmax=1)
    axes[1, 0].set_title(f'Transmisia rafinată (t_min = {t_min:.2f})')
    axes[1, 0].axis('off')

    axes[1, 1].imshow(J_restored_rgb)
    axes[1, 1].set_title('Imagine restaurată (J)')
    axes[1, 1].axis('off')

    axes[1, 2].hist(J_restored_rgb.ravel(), 256, range=[0, 255], density=True)
    axes[1, 2].set_title('Histograma imaginii restaurate')

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.show()



