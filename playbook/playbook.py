import re
from typing import Optional

from playbook.playbook_clone import SYSTEM_PROMPT as ORIGINAL_PLAYBOOK


# Aturan asli tetap di playbook_clone.py. Versi ini adalah ringkasan operasional
# untuk prompt LLM: semua kelompok aturan dipertahankan, sedangkan contoh dan
# penjelasan berulang dihilangkan agar payload audit tidak melebihi batas provider.
PLAYBOOK_RULES = """
B. KEPASTIAN DAN BATAS AUDIT
- Temuan harus berdasar DDL saja. Jangan mengarang tabel, kolom, relasi, opsi ENUM, kebutuhan bisnis, atau struktur metadata.
- Aturan PASTI selalu dilaporkan bila bukti DDL melanggar. Aturan TAFSIRAN hanya bila bukti kuat; Catatan wajib diawali
  "Tafsiran:" atau "Perlu verifikasi". Bila ragu jangan buat temuan.
- Tabel framework/paket tetap diaudit; Catatan harus menyebut perubahan perlu penyesuaian paket/konfigurasi atau pengecualian.
- Satu objek melanggar satu aturan = satu temuan. Jangan buat temuan untuk objek/aturan yang sudah benar, temuan generik tanpa objek,
  atau duplikat. Nama usulan harus konsisten dan maksimal 64 karakter.

C1. DATABASE (2b, 3b)
- Nama database: [aplikasi]_[dev|stage|prod]. Jika salah, satu temuan Nama database dengan Nama Tabel "-".
- Wajib ada metadata_database. Bila tidak ada, satu temuan Tabel metadata database.
- Tidak adanya CHECK secara global bukan temuan generik; buat CHECK spesifik hanya dengan bukti kuat.

C2. NAMA TABEL (2a, 2b)
- Tabel/view lowercase snake_case; tabel berupa kata benda tunggal. Nilai bentuk tunggal secara kata terakhir; jangan salahkan
  news, series, species, status, address, access, analytics, metrics.
- Tabel lookup/master wajib prefix master_; mst_/ref_/m_ salah. Pivot tetap singular dan deskriptif.
- Reserved word SQL dan singkatan tak baku (mis. trx, biblio) harus diganti kata lengkap. Usulan nama harus deskriptif.

C3. PRIMARY KEY (2b, 2c, 3a)
- Semua tabel punya PK bernama [nama_tabel_usulan]_id; id polos melanggar.
- PK master CHAR(36); non-master BIGINT UNSIGNED AUTO_INCREMENT. INT/SMALLINT, tanpa UNSIGNED/AUTO_INCREMENT,
  atau UUID non-master melanggar.
- PK komposit: temuan Tafsiran, usulkan surrogate PK dan kombinasi lama menjadi UNIQUE.
- Jika tabel master/PK berubah, FK yang merujuk wajib ikut nama dan tipe; sebutkan dampaknya.

C4. FOREIGN KEY (2b, 3a)
- Kolom relasi *_id atau bukti relasi kuat wajib FK, nama sama persis dengan PK target atau [peran]_[nama_pk].
- Jangan paksa FK pada pasangan polimorfik *_type+*_id, snapshot/riwayat, atau relasi yang tidak cukup bukti.
- FK harus kompatibel dengan PK target (tipe, panjang, UNSIGNED, collation), dan sebaiknya ber-index.
- created_by/updated_by/deleted_by mengikuti C10; bukan temuan nama FK biasa.

C5. NAMA KOLOM (2a, 2b)
- Kolom lowercase snake_case, tanpa spasi/huruf besar/tanda hubung, reserved word MySQL, singkatan tak baku, atau salah eja.
- Flag BOOLEAN/TINYINT(1) atau nilai 0/1, Y/N, Active/Inactive wajib prefix is_/has_/can_; flag dengan tipe lain adalah
  Tipe data flag boolean.
- TIMESTAMP/DATETIME wajib suffix _at; DATE wajib _date. Jangan ubah DATETIME menjadi DATE hanya demi suffix.
- Reserved sebenarnya: key, index, order, group, select, table, desc, range, rank, read, write, from, to, default,
  limit, option, values, condition, interval, primary, check, column, usage, load. Jangan tandai type/status/date/name/comment.

C6. TIPE DATA (2c)
- email VARCHAR(255); NIK/NIP/NRP/nip_lama VARCHAR(18); telepon/HP VARCHAR(20); kode pos CHAR(5).
- Nilai uang/gaji/harga/denda/saldo DECIMAL(13,4), bukan FLOAT/DOUBLE/INT.
- Status beropsi terbatas memakai ENUM atau FK referensi; flag boolean dikecualikan. Jangan mengarang opsi ENUM.
- PK/FK dan audit timestamp mengikuti C3, C4, C10.

C7. COMMENT DAN PII (3b)
- Setiap tabel wajib COMMENT. Kolom PII/sensitif wajib COMMENT.
- Kolom PII ber-COMMENT harus diawali [PII]; jika COMMENT tidak ada, hanya temuan COMMENT kolom sensitif, jangan gandakan tag.
- Password hash, token, secret, passcode, dan URL rahasia sensitif tetapi bukan PII; tetap wajib COMMENT tanpa tag PII.

C8. CONSTRAINT (3a)
- created_at/updated_at: TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP; updated_at juga ON UPDATE CURRENT_TIMESTAMP.
  Laporkan satu temuan per tabel untuk default audit bermasalah dan Catatan backfill sebelum NOT NULL.
- NOT NULL adalah Tafsiran dan perlu bukti kuat; NULL berarti belum diketahui. Periksa kontradiksi ON DELETE SET NULL.
- Email akun/orang dan NIK/NIP/NRP orang yang unik wajib UNIQUE. Nama unique [tabel_usulan]_[kolom]_uq.
- CHECK hanya dengan bukti kuat: nilai/radius/kapasitas/harga/denda/durasi, pasangan waktu, atau flag/status terbatas.
  Nama check [tabel_usulan]_[kolom]_chk.

C9. INDEX (2b)
- Index non-unique: idx_[tabel_usulan]_[kolom_berurutan]. Unique bukan Index biasa.
- Index biasa sama dengan PK/UNIQUE adalah Index redundan; hapus index biasa dan jangan juga laporkan nama index.
- Salah nama index/unique saja: solusi ALTER TABLE ... RENAME INDEX, bukan DROP/ADD.

C10. AUDIT TRAIL (4)
- Wajib: created_at TIMESTAMP, created_by VARCHAR(100), updated_at TIMESTAMP, updated_by VARCHAR(100),
  deleted_at TIMESTAMP NULL, is_deleted BOOLEAN.
- Kolom hilang: satu temuan Standard Field Audit Trail per tabel. Tipe salah: Tipe kolom audit trail.
- Untuk *_by, Catatan sebut konflik playbook VARCHAR(100) versus FK dan perlunya konfirmasi.

C11. VIEW (2b, 3b)
- View wajib prefix v_ dan lowercase snake_case.
- View yang menampilkan PII: satu temuan per view, sebut kolom dan tabel asal. Jangan masukkan nama referensi/non-PII.

C12. PII (1, 3b)
- PII mencakup identitas manusia: nama orang, username akun, email, telepon, alamat/kode pos pribadi, NIK/NIP/NRP/KTP/NPWP,
  lahir, gender, agama, pendidikan, foto/biometrik, IP/geolokasi pribadi, perangkat, dokumen/keterangan pribadi.
- Bukan PII: nama tabel referensi/status/kategori/jabatan/lokasi kantor/peran, kredensial teknis, konfigurasi, UUID teknis,
  flag, ID teknis/FK. name/nama hanya PII pada tabel orang; waktu seperti email_verified_at bukan PII.
- Bila ragu Status PII "Tidak" dan Catatan "Perlu verifikasi".

D. KONSISTENSI DAN LARANGAN
- Rename tabel harus mengalir ke PK, FK, index, unique, check, dan tipe FK master.
- Jangan hitung UNIQUE sebagai Index; jangan tandai FK polimorfik; jangan tandai nama referensi sebagai PII; jangan buat
  nama usulan kembar atau lebih dari 64 karakter.

F. NOMOR ATURAN OUTPUT
Isi "Aturan Playbook/UU" dengan tepat salah satu label lengkap berikut; jangan hanya menulis nomornya:
- 1. Klasifikasi data / tag PII
- 2a. Panduan penamaan universal
- 2b. Penamaan objek spesifik
- 2c. Tipe data baku
- 3a. Constraint
- 3b. Dokumentasi
- 4. Standard Field Audit Trail

Panduan cepat pemilihan aturan (bukan daftar temuan yang membatasi audit):
- Nama Primary Key, nama tabel/database/FK/index/unique/check/view memakai 2b. Penamaan objek spesifik.
  Jangan memakai 3a hanya karena objeknya bernama Primary Key.
- Tipe Primary Key dan tipe/ukuran data memakai 2c. Tipe data baku.
- Nama kolom, reserved word, serta penamaan flag boolean memakai 2a. Panduan penamaan universal.
- 3a. Constraint dipakai untuk PK/FK/UNIQUE/CHECK yang hilang atau tidak valid, serta DEFAULT/NOT NULL;
  3b. Dokumentasi untuk COMMENT/PII/metadata_database; 4 hanya untuk audit trail.
""".strip()


RULE_LABELS = {
    "1": "1. Klasifikasi data / tag PII",
    "2a": "2a. Panduan penamaan universal",
    "2b": "2b. Penamaan objek spesifik",
    "2c": "2c. Tipe data baku",
    "3a": "3a. Constraint",
    "3b": "3b. Dokumentasi",
    "4": "4. Standard Field Audit Trail",
}


def format_playbook_rule(value: str) -> Optional[str]:
    """Return the canonical display label for a valid playbook rule number."""
    match = re.match(r"^\s*(1|2a|2b|2c|3a|3b|4)\b", value, re.IGNORECASE)
    return RULE_LABELS.get(match.group(1).lower()) if match else None


_OBJECT_SECTION = (
    ORIGINAL_PLAYBOOK.split('"Objek Temuan": string, PILIH', 1)[1]
    .split('- "Aturan Playbook/UU"', 1)[0]
)
VALID_OBJECT_NAMES = frozenset(re.findall(r'"([^"]+)"', _OBJECT_SECTION))
