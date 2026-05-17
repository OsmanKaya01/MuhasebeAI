// dashboard.js
// Bu dosyada veri kaydetme / silme / hesaplama yoktur.
// JS sadece görünüm işlemleri için kullanılır.

let seciliCompanyId = null;

function goster(element) {
  if (element) {
    element.style.display = "block";
  }
}

function gizle(element) {
  if (element) {
    element.style.display = "none";
  }
}

function temizleInput(id) {
  const input = document.getElementById(id);
  if (input) {
    input.value = "";
  }
}

// ===============================
// ŞİRKET PANEL AÇMA
// ===============================

function sirketPanelAc(companyId, element) {
  seciliCompanyId = companyId;

  const paneller = document.querySelectorAll(".sirket-panel");
  const sirketler = document.querySelectorAll("#sirketListesi li");
  const raporAlani = document.getElementById("raporAlani");

  paneller.forEach(function (panel) {
    panel.style.display = "none";
  });

  sirketler.forEach(function (sirket) {
    sirket.classList.remove("aktif");
  });

  if (raporAlani) {
    raporAlani.style.display = "none";
  }

  const aktifPanel = document.getElementById("sirket-panel-" + companyId);

  if (aktifPanel) {
    aktifPanel.style.display = "block";
  }

  if (element) {
    element.classList.add("aktif");
  }
}

// ===============================
// TAB İŞLEMLERİ
// ===============================

function tabSec(prefix, sekme, buton) {
  const manuelAlan = document.getElementById(prefix + "-manuel");
  const dosyaAlan = document.getElementById(prefix + "-dosya");

  const panel = buton.closest(".panel");
  const tabButonlari = panel.querySelectorAll(".tab-btn");

  tabButonlari.forEach(function (btn) {
    btn.classList.remove("aktif-tab");
  });

  buton.classList.add("aktif-tab");

  if (sekme === "manuel") {
    if (manuelAlan) {
      manuelAlan.style.display = "block";
    }

    if (dosyaAlan) {
      dosyaAlan.style.display = "none";
    }
  }

  if (sekme === "dosya") {
    if (manuelAlan) {
      manuelAlan.style.display = "none";
    }

    if (dosyaAlan) {
      dosyaAlan.style.display = "block";
    }
  }
}

// ===============================
// DOSYA SEÇME / ÖNİZLEME
// ===============================

function dosyaSecildi(prefix, input) {
  const dosya = input.files[0];

  const dosyaAdiAlani = document.getElementById(prefix + "DosyaAdi");
  const onizlemeAlani = document.getElementById(prefix + "Onizleme");
  const dosyaAlan = document.getElementById(prefix + "DosyaAlan");

  if (!dosya) {
    if (dosyaAdiAlani) {
      dosyaAdiAlani.innerText = "";
    }

    if (onizlemeAlani) {
      onizlemeAlani.innerHTML = "";
    }

    if (dosyaAlan) {
      dosyaAlan.classList.remove("dosya-yuklendi");
    }

    return;
  }

  if (dosyaAdiAlani) {
    dosyaAdiAlani.innerText = dosya.name;
  }

  if (dosyaAlan) {
    dosyaAlan.classList.add("dosya-yuklendi");
  }

  if (!onizlemeAlani) {
    return;
  }

  onizlemeAlani.innerHTML = "";

  if (dosya.type.startsWith("image/")) {
    const img = document.createElement("img");

    img.src = URL.createObjectURL(dosya);
    img.alt = dosya.name;

    onizlemeAlani.appendChild(img);
  } else if (dosya.type === "application/pdf") {
    const pdfYazi = document.createElement("p");
    pdfYazi.innerText = "PDF seçildi";
    onizlemeAlani.appendChild(pdfYazi);
  }
}

// ===============================
// ŞİRKET EKLE MODAL
// ===============================

function sirketEkleFormAc() {
  const overlay = document.getElementById("sirketEkleOverlay");
  const modal = document.getElementById("sirketEkleModal");

  goster(overlay);
  goster(modal);

  setTimeout(function () {
    const input = document.getElementById("yeniSirketId");
    if (input) {
      input.focus();
    }
  }, 100);
}

function sirketEkleFormKapat() {
  const overlay = document.getElementById("sirketEkleOverlay");
  const modal = document.getElementById("sirketEkleModal");

  gizle(overlay);
  gizle(modal);

  temizleInput("yeniSirketId");
  temizleInput("yeniSirketAdi");
}

// ===============================
// ŞİRKET CONTEXT MENÜ
// ===============================

function sirketMenuAc(companyId, event) {
  seciliCompanyId = companyId;

  const menu = document.getElementById("sirketMenu");
  const silCompanyIdInput = document.getElementById("silCompanyId");

  if (silCompanyIdInput) {
    silCompanyIdInput.value = companyId;
  }

  if (!menu) {
    return;
  }

  menu.style.display = "block";
  menu.style.left = event.pageX + "px";
  menu.style.top = event.pageY + "px";
}

function sirketMenuKapat() {
  const menu = document.getElementById("sirketMenu");
  gizle(menu);
}

document.addEventListener("click", function (event) {
  const menu = document.getElementById("sirketMenu");

  if (!menu) {
    return;
  }

  if (!menu.contains(event.target)) {
    sirketMenuKapat();
  }
});

// ===============================
// ŞİRKET SİLME MODAL
// ===============================

function sirketiSilBaslat() {
  sirketMenuKapat();

  const overlay = document.getElementById("sifreOverlay");
  const modal = document.getElementById("sifreModal");
  const silCompanyIdInput = document.getElementById("silCompanyId");

  if (silCompanyIdInput && seciliCompanyId) {
    silCompanyIdInput.value = seciliCompanyId;
  }

  goster(overlay);
  goster(modal);

  setTimeout(function () {
    const input = document.getElementById("silSifre");
    if (input) {
      input.focus();
    }
  }, 100);
}

function sifreModalKapat() {
  const overlay = document.getElementById("sifreOverlay");
  const modal = document.getElementById("sifreModal");

  gizle(overlay);
  gizle(modal);

  temizleInput("silSifre");
}

// ===============================
// RAPOR ALANI
// ===============================

function aktifCompanyIdBul() {
  if (seciliCompanyId) {
    return seciliCompanyId;
  }

  const aktifSirket = document.querySelector("#sirketListesi li.aktif");

  if (aktifSirket) {
    const panelId = aktifSirket.getAttribute("onclick");

    if (panelId) {
      const eslesme = panelId.match(/sirketPanelAc\('([^']+)'/);

      if (eslesme) {
        return eslesme[1];
      }
    }
  }

  const ilkPanel = document.querySelector(".sirket-panel");

  if (ilkPanel && ilkPanel.id) {
    return ilkPanel.id.replace("sirket-panel-", "");
  }

  return null;
}

function raporAc(raporTipi, baslik) {
  const companyId = aktifCompanyIdBul();
  const sirketPanelleri = document.querySelectorAll(".sirket-panel");
  const raporAlani = document.getElementById("raporAlani");
  const raporBaslik = document.getElementById("raporBaslik");
  const raporIcerik = document.getElementById("raporIcerik");

  if (!companyId || !raporAlani || !raporIcerik) {
    return;
  }

  const kaynak = document.getElementById(raporTipi + "-rapor-" + companyId);

  sirketPanelleri.forEach(function (panel) {
    panel.style.display = "none";
  });

  if (raporBaslik) {
    raporBaslik.innerText = baslik;
  }

  if (kaynak) {
    raporIcerik.innerHTML = kaynak.innerHTML;
  } else {
    raporIcerik.innerHTML = "<p>Bu şirket için rapor bulunamadı.</p>";
  }

  goster(raporAlani);
}

function gunlukRaporGoster() {
  sirketMenuKapat();
  raporAc("gunluk", "Günlük Rapor");
}

function aylikRaporGoster() {
  sirketMenuKapat();
  raporAc("aylik", "Aylık Rapor");
}

function raporKapat() {
  const raporAlani = document.getElementById("raporAlani");
  const raporIcerik = document.getElementById("raporIcerik");

  gizle(raporAlani);

  if (raporIcerik) {
    raporIcerik.innerHTML = "";
  }

  const aktifSirket = document.querySelector("#sirketListesi li.aktif");

  if (aktifSirket) {
    aktifSirket.click();
    return;
  }

  const ilkSirket = document.querySelector("#sirketListesi li");
  if (ilkSirket && ilkSirket.querySelector(".sirket-adi-text")) {
    ilkSirket.click();
  }
}

// ===============================
// FİŞ / FATURA MODAL
// ===============================

function fisModalAc(icerik) {
  const overlay = document.getElementById("fisOverlay");
  const modal = document.getElementById("fisModal");
  const fisIcerik = document.getElementById("fisIcerik");

  if (fisIcerik) {
    fisIcerik.innerHTML = icerik || "";
  }

  goster(overlay);
  goster(modal);
}

function fisModalKapat() {
  const overlay = document.getElementById("fisOverlay");
  const modal = document.getElementById("fisModal");
  const fisIcerik = document.getElementById("fisIcerik");

  gizle(overlay);
  gizle(modal);

  if (fisIcerik) {
    fisIcerik.innerHTML = "";
  }
}

// ===============================
// SAYFA YÜKLENİNCE
// ===============================

document.addEventListener("DOMContentLoaded", function () {
  const aktifSirket = document.querySelector("#sirketListesi li.aktif");

  if (aktifSirket && aktifSirket.querySelector(".sirket-adi-text")) {
    aktifSirket.click();
    return;
  }

  const ilkSirket = document.querySelector("#sirketListesi li");
  if (ilkSirket && ilkSirket.querySelector(".sirket-adi-text")) {
    ilkSirket.click();
  }
});

// ===============================
// AI yükleniyor
// ===============================

function loadingGoster() {
  const loadingOverlay = document.getElementById("loadingOverlay");

  if (loadingOverlay) {
    loadingOverlay.style.display = "flex";
  }
}