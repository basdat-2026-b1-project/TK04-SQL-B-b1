from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.humanize.templatetags.humanize import intcomma
from datetime import date
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from django.db import connection, transaction
from datetime import date

DUMMY_IDENTITAS = [
    {'nomor': 'A12345678', 'jenis': 'Paspor', 'negara': 'Indonesia',
     'tanggal_terbit': '2020-01-15', 'tanggal_habis': '2030-01-15', 'status': 'Aktif'},
    {'nomor': '327501234567890', 'jenis': 'KTP', 'negara': 'Indonesia',
     'tanggal_terbit': '2019-06-01', 'tanggal_habis': '2024-06-01', 'status': 'Kedaluwarsa'},
    {'nomor': 'SIM0001', 'jenis': 'SIM', 'negara': 'Indonesia',
     'tanggal_terbit': '2023-03-10', 'tanggal_habis': '2028-03-10', 'status': 'Aktif'},
]

DUMMY_MASKAPAI = [
    ('GA', 'GA - Garuda Indonesia'),
    ('QG', 'QG - Citilink'),
    ('JT', 'JT - Lion Air'),
    ('ID', 'ID - Batik Air'),
    ('SQ', 'SQ - Singapore Airlines'),
]

DUMMY_BANDARA = [
    ('CGK', 'CGK - Soekarno-Hatta, Jakarta'),
    ('DPS', 'DPS - Ngurah Rai, Bali'),
    ('SUB', 'SUB - Juanda, Surabaya'),
    ('SIN', 'SIN - Changi, Singapore'),
    ('NRT', 'NRT - Narita, Tokyo'),
    ('KUL', 'KUL - KLIA, Kuala Lumpur'),
    ('BKK', 'BKK - Suvarnabhumi, Bangkok'),
    ('HKG', 'HKG - Chek Lap Kok, Hong Kong'),
    ('SYD', 'SYD - Kingsford Smith, Sydney'),
    ('ICN', 'ICN - Incheon, Seoul'),
]

DUMMY_KLAIM = [
    {'id': 'CLM-001', 'maskapai': 'GA', 'rute': 'CGK → DPS',
     'tanggal': '2024-10-01', 'flight': 'GA404', 'kelas': 'Business',
     'status': 'Disetujui', 'timestamp': '2024-10-05 18:45:00'},
    {'id': 'CLM-002', 'maskapai': 'SQ', 'rute': 'SIN → NRT',
     'tanggal': '2024-11-15', 'flight': 'SQ12', 'kelas': 'Economy',
     'status': 'Menunggu', 'timestamp': '2024-11-20 18:45:00'},
    {'id': 'CLM-003', 'maskapai': 'GA', 'rute': 'CGK → SUB',
     'tanggal': '2025-01-10', 'flight': 'GA202', 'kelas': 'Economy',
     'status': 'Ditolak', 'timestamp': '2025-01-12 09:30:00'},
]

DUMMY_TRANSFER = [
    {'timestamp': '2025-01-15 10:30', 'member': 'Jane Smith',
     'email': 'jane@example.com', 'jumlah': -5000, 'catatan': 'Hadiah ulang tahun', 'tipe': 'Kirim'},
    {'timestamp': '2025-02-01 14:00', 'member': 'Budi A. Santoso',
     'email': 'budi@example.com', 'jumlah': 2000, 'catatan': '-', 'tipe': 'Terima'},
]

DUMMY_HADIAH = [
    {'kode': 'RWD-001', 'nama': 'Tiket Domestik PP', 'penyedia': 'Garuda Indonesia',
     'miles': 15000, 'deskripsi': 'Tiket pulang-pergi rute domestik Indonesia',
     'valid_start': '2024-01-01', 'program_end': '2025-12-31'},
    {'kode': 'RWD-002', 'nama': 'Upgrade Business Class', 'penyedia': 'Garuda Indonesia',
     'miles': 25000, 'deskripsi': 'Upgrade dari economy ke business class',
     'valid_start': '2026-01-01', 'program_end': '2027-01-01'},
    {'kode': 'RWD-003', 'nama': 'Voucher Hotel Rp500.000', 'penyedia': 'TravelokaPartner',
     'miles': 8000, 'deskripsi': 'Voucher hotel berlaku di seluruh Indonesia',
     'valid_start': '2024-06-01', 'program_end': '2025-06-30'},
    {'kode': 'RWD-004', 'nama': 'Akses Lounge 1x', 'penyedia': 'Plaza Premium',
     'miles': 3000, 'deskripsi': 'Akses lounge bandara premium 1 kali kunjungan',
     'valid_start': '2024-01-01', 'program_end': '2025-12-31'},
    {'kode': 'RWD-005', 'nama': 'Extra Bagasi 10kg', 'penyedia': 'Garuda Indonesia',
     'miles': 5000, 'deskripsi': 'Tambahan bagasi 10kg untuk 1 penerbangan',
     'valid_start': '2025-01-01', 'program_end': '2026-12-31'},
]

DUMMY_RIWAYAT_REDEEM = [
    {'hadiah': 'Akses Lounge 1x', 'timestamp': '2025-01-20 16:00', 'miles': -3000},
]

DUMMY_PACKAGES = [
    {'id': 'AMP-001', 'miles': 1000, 'harga': 'Rp 150.000'},
    {'id': 'AMP-002', 'miles': 5000, 'harga': 'Rp 650.000'},
    {'id': 'AMP-003', 'miles': 10000, 'harga': 'Rp 1.200.000'},
    {'id': 'AMP-004', 'miles': 25000, 'harga': 'Rp 2.750.000'},
    {'id': 'AMP-005', 'miles': 50000, 'harga': 'Rp 5.000.000'},
]

DUMMY_TIERS = [
    {'id': 'BLUE', 'nama': 'Blue', 'min_frekuensi': 0, 'min_miles': 0,
     'keuntungan': ['Akumulasi miles dasar', 'Akses penawaran khusus member']},
    {'id': 'SILVER', 'nama': 'Silver', 'min_frekuensi': 10, 'min_miles': 15000,
     'keuntungan': ['Bonus miles 25%', 'Priority check-in', 'Akses lounge partner']},
    {'id': 'GOLD', 'nama': 'Gold', 'min_frekuensi': 25, 'min_miles': 40000,
     'keuntungan': ['Bonus miles 50%', 'Priority boarding', 'Akses lounge premium', 'Extra bagasi 10kg']},
    {'id': 'PLATINUM', 'nama': 'Platinum', 'min_frekuensi': 50, 'min_miles': 80000,
     'keuntungan': ['Bonus miles 100%', 'Upgrade gratis', 'Akses lounge first class', 'Extra bagasi 20kg', 'Dedicated hotline']},
]

def login_required_member(view_func):
    """Simple decorator untuk cek session member"""
    def wrapper(request, *args, **kwargs):
        if not request.session.get('role'):
            return redirect('accounts:login')
        if request.session.get('role') != 'member':
            return redirect('accounts:dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required_member
def identitas_view(request):
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'tambah':
            nomor = request.POST.get('nomor')

            sudah_ada = any(i['nomor'] == nomor for i in DUMMY_IDENTITAS)
            if sudah_ada:
                messages.error(request, 'Nomor dokumen sudah terdaftar.')
            else:
                DUMMY_IDENTITAS.append({
                    'nomor': nomor,
                    'jenis': request.POST.get('jenis'),
                    'negara': request.POST.get('negara'),
                    'tanggal_terbit': request.POST.get('tanggal_terbit'),
                    'tanggal_habis': request.POST.get('tanggal_habis'),
                    'status': 'Aktif',
                })
                messages.success(request, 'Identitas berhasil ditambahkan.')

        elif action == 'edit':
            nomor = request.POST.get('nomor')

            for identitas in DUMMY_IDENTITAS:
                if identitas['nomor'] == nomor:
                    identitas['jenis'] = request.POST.get('jenis')
                    identitas['negara'] = request.POST.get('negara')
                    identitas['tanggal_terbit'] = request.POST.get('tanggal_terbit')
                    identitas['tanggal_habis'] = request.POST.get('tanggal_habis')
                    identitas['status'] = request.POST.get('status', 'Aktif')
                    break

            messages.success(request, 'Identitas berhasil diperbarui.')

        elif action == 'hapus':
            nomor = request.POST.get('nomor')

            for identitas in DUMMY_IDENTITAS:
                if identitas['nomor'] == nomor:
                    DUMMY_IDENTITAS.remove(identitas)
                    break

            messages.success(request, 'Identitas berhasil dihapus.')

        return redirect('member:identitas')

    today = date.today()

    for identitas in DUMMY_IDENTITAS:
        tanggal_habis = date.fromisoformat(identitas['tanggal_habis'])

        if today > tanggal_habis:
            identitas['status'] = 'Kedaluwarsa'
        else:
            identitas['status'] = 'Aktif'

    return render(request, 'member/identitas.html', {
        'identitas_list': DUMMY_IDENTITAS,
    })

def claim_list(request):
    filter_status = request.GET.get('status', 'Semua')

    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'ajukan':
            maskapai = request.POST.get('maskapai')
            kelas = request.POST.get('kelas')
            asal = request.POST.get('asal')
            tujuan = request.POST.get('tujuan')
            tanggal = request.POST.get('tanggal')
            flight_number = request.POST.get('flight_number')
            nomor_tiket = request.POST.get('nomor_tiket')
            pnr = request.POST.get('pnr')

            messages.success(request, f'Klaim untuk penerbangan {flight_number} ({asal} - {tujuan}) berhasil diajukan.')
            return redirect('member:claim_list')
        
        elif action == 'edit':
            status_klaim = request.POST.get('status_saat_ini') 
            if status_klaim == 'Menunggu':
                messages.success(request, 'Klaim berhasil diperbarui.')
            else:
                messages.error(request, 'Klaim yang sudah Disetujui atau Ditolak tidak dapat diubah.')
        
        elif action == 'batalkan':
            status_klaim = request.POST.get('status_saat_ini')
            if status_klaim == 'Menunggu':
                messages.success(request, 'Klaim berhasil dibatalkan.')
            else:
                messages.error(request, 'Klaim sudah diproses, tidak bisa dibatalkan.')
        
        return redirect('member:claim_list') 

    # R - Riwayat Klaim
    klaim_list_filtered = DUMMY_KLAIM
    if filter_status != 'Semua':
        klaim_list_filtered = [k for k in DUMMY_KLAIM if k['status'] == filter_status]

    return render(request, 'member/klaim.html', {
        'klaim_list': klaim_list_filtered,
        'filter_status': filter_status,
        'status_choices': ['Semua', 'Menunggu', 'Disetujui', 'Ditolak'],
    })

def transfer_view(request):
    member_dummy = {
        'nama_lengkap': 'Nisrina Alya',
        'email_pengguna': 'nisrina.alya@ui.ac.id',
        'award_miles': 32000
    }

    if request.method == 'POST':
        email_penerima = request.POST.get('email_penerima', '').strip()
        jumlah_raw = request.POST.get('jumlah', 0)
        catatan = request.POST.get('catatan', '')

        try:
            jumlah = int(jumlah_raw)
        except ValueError:
            messages.error(request, 'Jumlah miles harus berupa angka.')
            return redirect('member:transfer')

        if email_penerima == member_dummy['email_pengguna']:
            messages.error(request, 'Member tidak dapat mentransfer miles ke dirinya sendiri.')
        elif jumlah <= 0:
            messages.error(request, 'Jumlah miles harus lebih dari 0.')
        elif jumlah > member_dummy['award_miles']:
            messages.error(request, f'Award miles tidak mencukupi. Saldo Anda: {member_dummy["award_miles"]} miles.')
        else:
            messages.success(request, f'Berhasil transfer {jumlah} miles ke {email_penerima}.')
        
        return redirect('member:transfer')

    return render(request, 'member/transfer.html', {
        'member': member_dummy,
        'transfer_list': DUMMY_TRANSFER,
        'email_session': member_dummy['email_pengguna']
    })


login_required_member
def redeem_view(request):
    active_tab = request.GET.get('tab', 'katalog')

    if request.method == 'POST':
        kode = request.POST.get('kode_hadiah')
        hadiah = next((h for h in DUMMY_HADIAH if h['kode'] == kode), None)
        if hadiah:
            award_miles = request.session.get('award_miles', 0)
            if award_miles < hadiah['miles']:
                messages.error(request, f'Award miles tidak mencukupi. Dibutuhkan {hadiah["miles"]} miles.')
            else:
                messages.success(request, f'Berhasil redeem "{hadiah["nama"]}" dengan {hadiah["miles"]} miles.')
        return redirect('member:redeem')

    return render(request, 'member/redeem.html', {
        'hadiah_list': DUMMY_HADIAH,
        'riwayat_redeem': DUMMY_RIWAYAT_REDEEM,
        'active_tab': active_tab,
    })

@login_required_member
def dashboard(request):
    # Mengambil data dinamis dari session user yang sedang login
    # Gunakan .get() dan nilai default agar tidak error jika session kosong
    context = {
        'nama': request.session.get('nama', 'Nama Belum Diatur'),
        'email': request.session.get('email', 'Email Belum Diatur'),
        'telepon': request.session.get('mobile_number', '-'), 
        'kewarganegaraan': request.session.get('kewarganegaraan', 'Indonesia'),
        'tanggal_lahir': request.session.get('tanggal_lahir', '-'),

        # Stat Cards
        'nomor_member': request.session.get('nomor_member', 'Belum Ada'),
        'tier': request.session.get('tier', 'BLUE'),
        'total_miles': request.session.get('total_miles', 0),
        'award_miles': request.session.get('award_miles', 0),

        # latest transaction (dummy) -> To Be Updated
        'transaksi': [
            {'tipe': 'Transfer', 'tanggal': '2026-04-26 10:31:20', 'miles': -1000},
            {'tipe': 'Redeem',   'tanggal': '2026-04-26 10:31:20', 'miles': -10000},
            {'tipe': 'Package',  'tanggal': '2026-04-26 10:31:20', 'miles': +16000},
            {'tipe': 'Package',  'tanggal': '2026-04-26 10:31:20', 'miles': +16000},
            {'tipe': 'Redeem',   'tanggal': '2026-04-26 10:31:20', 'miles': -10000},
        ],
    }
    return render(request, 'member/dashboard.html', context)


def login_required_member(view_func):
    """Decorator – cek session member."""
    def wrapper(request, *args, **kwargs):
        if not request.session.get('role'):
            return redirect('accounts:login')
        if request.session.get('role') != 'member':
            return redirect('accounts:dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def login_required_staf(view_func):
    """Decorator – cek session staf."""
    def wrapper(request, *args, **kwargs):
        if not request.session.get('role'):
            return redirect('accounts:login')
        if request.session.get('role') != 'staf':
            return redirect('accounts:dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required_member
def redeem_view(request):
    """
    Katalog hadiah + riwayat redeem milik member yang sedang login.

    Tabel:
        hadiah              (kode_hadiah, nama, miles, deskripsi, valid_start_date, program_end, id_penyedia)
        redeem              (email_member, kode_hadiah, timestamp)
        penyedia / mitra    (untuk nama penyedia)
    """
    email_member = request.session.get('email')
    active_tab = request.GET.get('tab', 'katalog')

    # ── POST: proses redeem ──────────────────────────────────
    if request.method == 'POST':
        kode = request.POST.get('kode_hadiah', '').strip()

        try:
            with transaction.atomic():
                with connection.cursor() as cur:
                    # Ambil data hadiah
                    cur.execute("""
                        SELECT kode_hadiah, nama, miles
                        FROM hadiah
                        WHERE kode_hadiah = %s
                    """, [kode])

                    hadiah_row = cur.fetchone()

                    if not hadiah_row:
                        messages.error(request, 'Hadiah tidak ditemukan.')
                        return redirect('member:redeem')

                    kode_hadiah, nama_hadiah, miles_dibutuhkan = hadiah_row

                    # Lock saldo member
                    cur.execute("""
                        SELECT award_miles
                        FROM member
                        WHERE email = %s
                        FOR UPDATE
                    """, [email_member])

                    member_row = cur.fetchone()

                    award_miles = member_row[0] if member_row else 0

                    # Validasi saldo
                    if award_miles < miles_dibutuhkan:
                        messages.error(
                            request,
                            f'Award miles tidak mencukupi. '
                            f'Dibutuhkan {miles_dibutuhkan:,} miles, '
                            f'saldo Anda {award_miles:,} miles.'
                        )
                        return redirect('member:redeem')

                    now = timezone.now()

                    # Insert redeem
                    cur.execute("""
                        INSERT INTO redeem (
                            email_member,
                            kode_hadiah,
                            timestamp
                        )
                        VALUES (%s, %s, %s)
                    """, [email_member, kode_hadiah, now])

                    # Kurangi miles
                    cur.execute("""
                        UPDATE member
                        SET award_miles = award_miles - %s
                        WHERE email = %s
                    """, [miles_dibutuhkan, email_member])

                    saldo_baru = award_miles - miles_dibutuhkan

            # Sync session
            request.session['award_miles'] = saldo_baru

            messages.success(
                request,
                f'Berhasil redeem "{nama_hadiah}" '
                f'dengan {miles_dibutuhkan:,} miles.'
            )

        except Exception:
            messages.error(request, 'Terjadi kesalahan saat redeem hadiah.')

        return redirect('member:redeem')

    # ── GET: tampilkan katalog & riwayat ────────────────────
    today = date.today()

    # Katalog hadiah aktif
    with connection.cursor() as cur:
        cur.execute("""
            SELECT
                h.kode_hadiah,
                h.nama,
                h.miles,
                h.deskripsi,
                h.valid_start_date,
                h.program_end,
                COALESCE(m.nama_mitra, 'Mitra') AS nama_penyedia
            FROM hadiah h
            LEFT JOIN mitra m
                ON m.id_penyedia = h.id_penyedia
            WHERE h.program_end >= %s
            ORDER BY h.miles ASC
        """, [today])

        cols = [c.name for c in cur.description]

        hadiah_list = [
            dict(zip(cols, row))
            for row in cur.fetchall()
        ]

    # Riwayat redeem
    with connection.cursor() as cur:
        cur.execute("""
            SELECT
                r.timestamp,
                h.nama AS nama_hadiah,
                h.miles AS miles_digunakan,
                r.kode_hadiah
            FROM redeem r
            JOIN hadiah h
                ON h.kode_hadiah = r.kode_hadiah
            WHERE r.email_member = %s
            ORDER BY r.timestamp DESC
        """, [email_member])

        cols = [c.name for c in cur.description]

        riwayat_redeem = [
            dict(zip(cols, row))
            for row in cur.fetchall()
        ]

    # Saldo terkini
    with connection.cursor() as cur:
        cur.execute("""
            SELECT award_miles
            FROM member
            WHERE email = %s
        """, [email_member])

        row = cur.fetchone()
        award_miles = row[0] if row else 0

    request.session['award_miles'] = award_miles

    return render(request, 'member/redeem.html', {
        'hadiah_list': hadiah_list,
        'riwayat_redeem': riwayat_redeem,
        'active_tab': active_tab,
        'award_miles': award_miles,
    })


@login_required_member
def package_view(request):
    """
    Daftar paket award miles + riwayat pembelian member.

    Tabel:
        award_miles_package         (id, harga_paket, jumlah_award_miles)
        member_award_miles_package  (id_award_miles_package, email_member, timestamp)
    """
    email_member = request.session.get('email')

    # ── POST: beli package ──────────────────────────────────
    if request.method == 'POST':
        pkg_id = request.POST.get('package_id', '').strip()

        try:
            with transaction.atomic():
                with connection.cursor() as cur:

                    # Ambil data package
                    cur.execute("""
                        SELECT
                            id,
                            harga_paket,
                            jumlah_award_miles
                        FROM award_miles_package
                        WHERE id = %s
                    """, [pkg_id])

                    row = cur.fetchone()

                    if not row:
                        messages.error(request, 'Paket tidak ditemukan.')
                        return redirect('member:package')

                    pkg_id_db, harga_paket, jumlah_award_miles = row

                    now = timezone.now()

                    # Simpan riwayat pembelian
                    cur.execute("""
                        INSERT INTO member_award_miles_package (
                            id_award_miles_package,
                            email_member,
                            timestamp
                        )
                        VALUES (%s, %s, %s)
                    """, [
                        pkg_id_db,
                        email_member,
                        now
                    ])

                    # Tambah award miles
                    cur.execute("""
                        UPDATE member
                        SET award_miles = award_miles + %s
                        WHERE email = %s
                    """, [
                        jumlah_award_miles,
                        email_member
                    ])

                    # Ambil saldo terbaru
                    cur.execute("""
                        SELECT award_miles
                        FROM member
                        WHERE email = %s
                    """, [email_member])

                    saldo_baru = cur.fetchone()[0]

            # Sync session
            request.session['award_miles'] = saldo_baru

            messages.success(
                request,
                f'Berhasil membeli '
                f'{jumlah_award_miles:,} Award Miles '
                f'seharga Rp {int(harga_paket):,}.'.replace(',', '.')
            )

        except Exception:
            messages.error(request, 'Terjadi kesalahan saat membeli package.')

        return redirect('member:package')

    # ── GET: daftar package ─────────────────────────────────
    with connection.cursor() as cur:
        cur.execute("""
            SELECT
                id,
                harga_paket,
                jumlah_award_miles
            FROM award_miles_package
            ORDER BY jumlah_award_miles ASC
        """)

        cols = [c.name for c in cur.description]

        packages = [
            dict(zip(cols, row))
            for row in cur.fetchall()
        ]

    # Riwayat pembelian package
    with connection.cursor() as cur:
        cur.execute("""
            SELECT
                mp.timestamp,
                p.id AS package_id,
                p.jumlah_award_miles,
                p.harga_paket
            FROM member_award_miles_package mp
            JOIN award_miles_package p
                ON p.id = mp.id_award_miles_package
            WHERE mp.email_member = %s
            ORDER BY mp.timestamp DESC
        """, [email_member])

        cols = [c.name for c in cur.description]

        riwayat_package = [
            dict(zip(cols, row))
            for row in cur.fetchall()
        ]

    # Ambil saldo terbaru
    with connection.cursor() as cur:
        cur.execute("""
            SELECT award_miles
            FROM member
            WHERE email = %s
        """, [email_member])

        row = cur.fetchone()
        award_miles = row[0] if row else 0

    request.session['award_miles'] = award_miles

    return render(request, 'member/package.html', {
        'packages': packages,
        'riwayat_package': riwayat_package,
        'award_miles': award_miles,
    })


@login_required_member
def info_tier_view(request):
    """
    Tampilkan semua tier beserta keuntungan,
    posisi member saat ini,
    dan progress ke tier berikutnya.
    """

    email_member = request.session.get('email')

    # Ambil semua tier
    with connection.cursor() as cur:
        cur.execute("""
            SELECT
                id_tier,
                nama,
                minimal_frekuensi_terbang,
                minimal_tier_miles
            FROM tier
            ORDER BY minimal_tier_miles ASC
        """)

        rows = cur.fetchall()

        tiers = [
            {
                'id_tier': r[0],
                'nama': r[1],
                'minimal_frekuensi_terbang': r[2],
                'minimal_tier_miles': r[3],
                'keuntungan': keuntungan_tier(r[1]),
            }
            for r in rows
        ]

    # Data member
    with connection.cursor() as cur:
        cur.execute("""
            SELECT
                id_tier,
                total_miles
            FROM member
            WHERE email = %s
        """, [email_member])

        row = cur.fetchone()

    current_id_tier = row[0] if row else 'T01'
    total_miles = row[1] if row else 0

    # Cari tier sekarang
    tier_ids = [t['id_tier'] for t in tiers]

    current_idx = (
        tier_ids.index(current_id_tier)
        if current_id_tier in tier_ids
        else 0
    )

    current_tier_obj = tiers[current_idx]

    next_tier = (
        tiers[current_idx + 1]
        if current_idx < len(tiers) - 1
        else None
    )

    # Progress %
    progress_pct = 0

    if next_tier:
        curr_min = current_tier_obj['minimal_tier_miles']
        next_min = next_tier['minimal_tier_miles']

        if next_min > curr_min:
            progress_pct = max(
                0,
                min(
                    100,
                    int(
                        (total_miles - curr_min)
                        / (next_min - curr_min)
                        * 100
                    )
                )
            )

    return render(request, 'member/info_tier.html', {
        'tiers': tiers,
        'current_tier': current_tier_obj,
        'next_tier': next_tier,
        'total_miles': total_miles,
        'progress_pct': progress_pct,
    })


def keuntungan_tier(nama_tier: str) -> list[str]:
    """
    Mapping nama tier → list keuntungan
    """

    mapping = {
        'Blue': [
            'Akumulasi miles dasar',
            'Akses penawaran khusus member',
        ],

        'Silver': [
            'Bonus miles 25%',
            'Priority check-in',
            'Akses lounge partner',
        ],

        'Gold': [
            'Bonus miles 50%',
            'Priority boarding',
            'Akses lounge premium',
            'Extra bagasi 10kg',
        ],

        'Platinum': [
            'Bonus miles 100%',
            'Upgrade gratis',
            'Akses lounge first class',
            'Extra bagasi 20kg',
            'Dedicated hotline',
        ],
    }

    return mapping.get(nama_tier, [])

def keuntungan_tier(nama_tier: str) -> list[str]:
    """Mapping nama tier → list keuntungan (tidak ada tabel di DB)."""
    mapping = {
        'Blue'    : ['Akumulasi miles dasar', 'Akses penawaran khusus member'],
        'Silver'  : ['Bonus miles 25%', 'Priority check-in', 'Akses lounge partner'],
        'Gold'    : ['Bonus miles 50%', 'Priority boarding', 'Akses lounge premium', 'Extra bagasi 10kg'],
        'Platinum': ['Bonus miles 100%', 'Upgrade gratis', 'Akses lounge first class',
                     'Extra bagasi 20kg', 'Dedicated hotline'],
    }
    return mapping.get(nama_tier, [])
