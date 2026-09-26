# Incidents

## I-001 (Amend İhlali)
- **Ne oldu:** T4-R aşamasında `git commit --amend` kullanılarak geçmiş değiştirildi.
- **Neden oldu:** Hatalı bir commit veya eksik dosyalar fark edildiğinde, yeni bir düzeltme commiti atmak yerine eski commiti ezmek tercih edildi, ancak bu denetim izini (audit trail) bozdu.
- **Bir daha nasıl önlenecek:** `--amend` komutunun kullanımı kesinlikle yasaklanmış kurallar arasındadır. Yapılan her hata veya eksiklik, şeffaflık gereği yeni bir commit ile (örn. `fix:` veya `chore:`) geçmişe eklenerek düzeltilecektir.

## I-002 (Hijyen İhlali)
- **Ne oldu:** Geçici çalışma dosyaları (`scratch/` dizini, `out1.json`, `out2.json`) çalışma ağacında (working tree) temizlenmeden bırakıldı.
- **Neden oldu:** Kanıt üretmek için oluşturulan geçici test çıktıları, commit öncesinde silinmesi unutuldu.
- **Bir daha nasıl önlenecek:** Her görev veya commit öncesinde `git status --short` komutu ile untracked (takip edilmeyen) veya kirli (dirty) dosyaların durumu kontrol edilecek ve geçici dosyalar projeye dahil edilmeden mutlak surette temizlenecektir.
