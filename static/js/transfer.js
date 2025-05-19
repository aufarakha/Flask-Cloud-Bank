const nominalInput = document.getElementById('nominalTransfer');
  const errorMessage = document.getElementById('error-message');

  nominalInput.addEventListener('input', function() {
    const value = parseInt(this.value);

    if (value < 50000) {
      errorMessage.textContent = "Minimal transfer Rp 50.000";
    } else {
      errorMessage.textContent = "";
    }
  });
  const rekeningInput = document.getElementById('nomorRekening');
  const errorRekening = document.getElementById('error-rekening');

  rekeningInput.addEventListener('input', function() {
    // Hapus semua karakter kecuali angka
    this.value = this.value.replace(/[^0-9]/g, '');

    // (Opsional) Validasi minimal panjang kalau mau
    if (this.value.length > 0 && this.value.length < 10) {
      errorRekening.textContent = "Nomor rekening minimal 10 digit";
    } else {
      errorRekening.textContent = "";
    }
  });
  